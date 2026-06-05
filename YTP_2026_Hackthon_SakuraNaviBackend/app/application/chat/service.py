"""Chat application service — orchestrates LLM client and tool executor."""

from datetime import datetime, timezone
from html import escape
import json
import uuid
from typing import Any, AsyncGenerator

import httpx

from app.application.chat.commands import (
    ChatStreamCommand,
    DeleteConversationCommand,
    DeleteMessageCommand,
    UpdateConversationCommand,
    UpdateMessageCommand,
)
from app.application.chat.ports import LLMClient, ToolExecutor
from app.domains.chat.entities import Conversation, Message
from app.domains.chat.repository import ChatRepository
from app.domains.chat.value_objects import (
    ChatUserId,
    ConversationId,
    MessageId,
    MessageRole,
)
from loguru import logger
from app.core.exceptions import ForbiddenException, ResourceNotFoundException

_MAX_AGENTIC_ROUNDS = 8
_MAX_HISTORY_MESSAGES = 12
_PERSONALIZATION_TOP_K = 3
_PERSONALIZATION_MAX_QUERY_CHARS = 600
_PERSONALIZATION_MAX_SNIPPET_CHARS = 220
_PERSONALIZATION_MAX_SKILLS = 5
_PERSONALIZATION_MAX_POSITIONS = 5
_EVIDENCE_FALLBACK_TEXT = (
    "目前查無相關具體資訊，請嘗試更精確關鍵字或稍後再試。\n"
    "⚠️ 細節以官方最新公告為準，建議申請前確認。"
)
SYSTEM_PROMPT = """<system_prompt>
  <role>你是 SakuraNavi，專為台灣青年設計的「行動導向」AI 顧問。</role>
  
  <objective>將政策、補助與職缺資訊，轉化為使用者能「直接申請或執行」的具體步驟與精準數據。</objective>

  <core_principles>
  <principle>語言強制要求：所有對話與輸出內容必須且僅能使用繁體中文（zh-TW）。</principle>
    <principle>意圖解析優先：洞察使用者隱含需求。若詢問「有什麼補助」，預設回答「適用項目、具體金額、申請步驟」，而非提供空泛清單。</principle>
    <principle>絕對具體：直接給出精確數字（金額、日期、名額），拒絕提供僅具導覽性質的廢話。</principle>
  </core_principles>

  <tool_execution_logic>
    <rule condition="問題屬性 IN [政策, 補助, 貸款, 實習津貼, 創業諮詢, 國際交流官方文件]">
      <action_1>優先呼叫 `search_knowledge_base`。</action_1>
      <action_2>IF 知識庫回傳為空 OR 資訊不足以組成完整行動指南 THEN 呼叫 `web_search` 進行補充。</action_2>
    </rule>
    <rule condition="問題屬性 IN [動態資訊, 即時職缺, 活動報名, 最新公告日期, 薪資動態]">
      <action_1>直接呼叫 `web_search`，不依賴知識庫。</action_1>
    </rule>
    <rule condition="使用者明確表示要撰寫履歷或優化履歷">
      <action_1>先呼叫 `start_resume_draft` 啟動草稿流程。</action_1>
      <action_2>之後每輪只問一題，將使用者回覆整理後用 `update_resume_draft` 寫入草稿。</action_2>
      <action_3>必填欄位（title、summary、skills、work_experiences）齊全後呼叫 `finalize_resume_draft` 產生正式履歷。</action_3>
      <action_4>完成後再詢問是否設為主要履歷；若同意，呼叫 `set_resume_primary`。</action_4>
    </rule>
    <rule condition="使用者明確表示要修改已有履歷">
      <action_1>先呼叫 `get_user_resumes` 取得使用者所有履歷，列出供使用者選擇。</action_1>
      <action_2>使用者指定履歷後，呼叫 `load_resume_for_edit` 載入該履歷。</action_2>
      <action_3>修改前**必須**先向使用者確認：「我打算把 [欄位] 改成 [新值]，是否確認？」</action_3>
      <action_4>收到「確認/好/可以/確定」才呼叫 `update_resume_draft`；收到「取消/不要/算了」則說「已取消，請告訴我你想怎麼修改」。</action_4>
    </rule>
  </tool_execution_logic>

  <search_strategy tool="web_search">
    <description>強制依問題類型優先使用 site operator 檢索。若官方網域查無可用結果，方可放寬為全網搜尋。</description>
    <mapping category="地方青年政策/創業/補助">site:youth.gov.taipei</mapping>
    <mapping category="全國青年政策/壯遊/就業">site:yda.gov.tw</mapping>
    <mapping category="求職/職缺/薪資行情">site:104.com.tw</mapping>
    <mapping category="獎學金/助學金/學貸">site:studentway.moe.gov.tw</mapping>
  </search_strategy>

  <output_schema>
    <format category="申請類">依序條列排版：[資格條件] → [補助內容與金額] → [截止日期] → [申請方式]</format>
    <format category="求職類">直接列出符合條件的職缺方向或直達連結。</format>
    <citation source="knowledge_base">句末標註 `(來源:{{filename}})`</citation>
    <citation source="web_search">句末標註 `([資料標題]({{URL}}))`</citation>
    <footer_statement>回答最末行強制輸出：`⚠️ 細節以官方最新公告為準，建議申請前確認。`</footer_statement>
  </output_schema>

  <negative_constraints>
    <constraint>禁止回覆「建議您至 XX 官網查詢」、「您可以考慮...」等不具備行動指引的模糊句型。</constraint>
    <constraint>禁止幻覺：若知識庫與網路搜尋皆查無明確數字、資格或日期，必須回答「目前查無相關具體資訊」，絕不可自行編造。</constraint>
  </negative_constraints>
</system_prompt>
"""


class ChatApplicationService:
    """Orchestrates streaming chat: LLM invocations + tool execution loop."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_executor: ToolExecutor,
        chat_repo: ChatRepository,
    ) -> None:
        self._llm = llm_client
        self._tool_executor = tool_executor
        self._chat_repo = chat_repo
        # Per-call buffer for in-flight MiniMax tool calls (partial data across chunks)
        self._tc_buffer: dict[str, dict] = {}

    async def stream_chat(
        self,
        cmd: ChatStreamCommand,
    ) -> AsyncGenerator[str, None]:
        """Stream SSE events for a chat interaction.

        Creates or loads the conversation, persists the user message,
        streams LLM + tool events, then persists the final assistant reply.

        Args:
            cmd: Immutable command carrying user_id, message, and optional conversation_id.

        Yields:
            SSE-formatted string lines (ready for StreamingResponse).
        """
        # Reset per-call tool call buffer for this conversation
        self._tc_buffer.clear()

        # 1. Resolve conversation — create new or validate ownership of existing
        user_id_vo = ChatUserId.from_str(cmd.user_id)
        if cmd.conversation_id:
            conv_id_vo = ConversationId.from_str(cmd.conversation_id)
            conversation = await self._chat_repo.find_conversation_by_id(conv_id_vo)
            if conversation is None or str(conversation.user_id().value) != cmd.user_id:
                logger.warning(
                    "[chat] Access denied: conv_id={} user_id={}",
                    cmd.conversation_id,
                    cmd.user_id,
                )
                yield f"data: {json.dumps({'type': 'error', 'code': 403, 'message': 'Conversation not found or access denied.'})}\n\n"
                return
            logger.info(
                "[chat] Continuing conversation: conv_id={}", cmd.conversation_id
            )
        else:
            conv_id_vo = ConversationId(uuid.uuid4())
            # Keep conversation title text-safe for downstream HTML rendering surfaces.
            safe_title = escape(cmd.message[:50], quote=False)
            conversation = Conversation(
                id=conv_id_vo,
                user_id=user_id_vo,
                title=safe_title,
            )
            await self._chat_repo.save_conversation(conversation)
            logger.info(
                "[chat] New conversation created: conv_id={} user_id={}",
                conv_id_vo,
                cmd.user_id,
            )

        # 2. Persist user message before streaming begins
        await self._chat_repo.save_message(
            Message(
                id=MessageId(uuid.uuid4()),
                conversation_id=conv_id_vo,
                role=MessageRole.USER,
                content=cmd.message,
            )
        )
        conversation.touch(datetime.now(tz=timezone.utc))
        await self._chat_repo.save_conversation(conversation)
        logger.debug("[chat] User message saved: conv_id={}", conv_id_vo)

        conv_id = str(conv_id_vo)
        # Pack conversation history (most recent N) so the LLM has context across turns.
        # find_messages_by_conversation returns rows newest-first (DESC); reverse so
        # the LLM receives chronological order (oldest → newest).
        # The just-saved user message is already included in the DB query result,
        # so we do NOT append it again below.
        history = await self._chat_repo.find_messages_by_conversation(
            conv_id_vo, limit=_MAX_HISTORY_MESSAGES
        )
        history = list(reversed(history))
        history_msgs: list[dict] = []
        for m in history:
            role = m.role().value if hasattr(m.role(), "value") else str(m.role())
            if role not in ("user", "assistant"):
                continue
            history_msgs.append({"role": role, "content": m.content()})
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        personalized_context = await self._build_personalized_rag_context(
            user_id=cmd.user_id,
            user_message=cmd.message,
            conversation_id=conv_id,
        )
        if personalized_context:
            messages.append({"role": "system", "content": personalized_context})
        messages.extend(history_msgs)
        assistant_text_parts: list[str] = []
        # Generate message ID before streaming so it's ready when done fires
        assistant_msg_id = uuid.uuid4()
        evidence_tools_called = False
        evidence_has_hits = False
        done_sent = False

        try:
            for _ in range(_MAX_AGENTIC_ROUNDS):
                tool_calls_this_round: list[dict] = []
                done_emitted = False
                round_text_parts: list[str] = []

                logger.debug(
                    "[chat] LLM stream started: conv_id={} messages={}",
                    conv_id,
                    len(messages),
                )
                async for event in self._llm.stream_chat(
                    messages, self._tool_executor.get_tool_definitions()
                ):
                    logger.debug(
                        "[llm→svc] raw event keys={} choices_count={}",
                        list(event.keys()),
                        len(event.get("choices", [])),
                    )
                    for choice in event.get("choices", []):
                        delta = choice.get("delta", {})
                        msg = choice.get("message", {})
                        tc_delta = delta.get("tool_calls")
                        tc_msg = msg.get("tool_calls")
                        logger.debug(
                            "[llm→svc] delta content={!r} delta tool_calls={} msg tool_calls={} finish_reason={}",
                            (delta.get("content") or "")[:80],
                            tc_delta,
                            tc_msg,
                            delta.get("finish_reason") or msg.get("finish_reason"),
                        )

                        # Text chunk — stream it
                        text = delta.get("content") or msg.get("content")
                        if text:
                            round_text_parts.append(text)
                            yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

                        # Tool calls — MiniMax sends partial tool call data across multiple SSE chunks.
                        # Each chunk for the same tool call shares the same 'index' but may omit
                        # 'id' in subsequent chunks (only the first chunk has id). The same
                        # dict reference is NOT mutated — each chunk is a separate dict object.
                        # We handle both 'delta' and 'msg' sources.
                        #
                        # Strategy: track in-flight tool calls by (index, name) when id is absent.
                        # When name+args are both populated, execute.
                        all_tc = []
                        if delta.get("tool_calls"):
                            all_tc.extend(delta["tool_calls"])
                        if msg.get("tool_calls"):
                            all_tc.extend(msg["tool_calls"])

                        for tc in all_tc:
                            tc_id = tc.get("id") or ""
                            fn = tc.get("function") or {}
                            name = fn.get("name") or ""
                            args = fn.get("arguments") or ""
                            index = tc.get("index")

                            # Build a buffer key: use tc_id if available,
                            # otherwise use (index, name) since index is always present.
                            #
                            # MiniMax sends tool call metadata across multiple SSE chunks:
                            #   Chunk 1: {id, name, index}      → id populated, args empty
                            #   Chunk 2: {index, args: ""}    → id missing, args starts filling
                            #   Chunk 3: {index, args: "{}"} → args complete, id still missing
                            #
                            # Strategy: When id is available, use it as key (most stable).
                            # When id is missing, find existing partial by index AND name
                            # (name must match to avoid merging different tool calls with same index).
                            #
                            # CRITICAL: We always track by index even when id is present,
                            # because subsequent chunks may not include the id.
                            if tc_id:
                                buf_key = tc_id
                                entry = self._tc_buffer.get(buf_key)
                                if entry is None:
                                    self._tc_buffer[buf_key] = {
                                        "id": tc_id,
                                        "index": index,
                                        "name": "",
                                        "arguments": "",
                                        "extra_content": tc.get("extra_content") or {},
                                    }
                                    entry = self._tc_buffer[buf_key]
                                # Also track by index for lookups when id is missing in later chunks
                                index_key = f"idx:{index}"
                                if index_key not in self._tc_buffer:
                                    self._tc_buffer[index_key] = entry
                            elif index is not None:
                                # No id — find existing partial by index only (index is always present).
                                # We use a single index-based key to avoid creating duplicate partials.
                                index_key = f"idx:{index}"
                                existing_entry = self._tc_buffer.get(index_key)
                                if existing_entry:
                                    buf_key = index_key
                                    entry = existing_entry
                                else:
                                    name_part = name or "?"
                                    buf_key = f"idx:{index}:{name_part}"
                                    self._tc_buffer[buf_key] = {
                                        "id": tc_id,
                                        "index": index,
                                        "name": name or "",
                                        "arguments": "",
                                        "extra_content": tc.get("extra_content") or {},
                                    }
                                    entry = self._tc_buffer[buf_key]
                                    # Also index by index for subsequent lookups without id
                                    self._tc_buffer[index_key] = entry
                            else:
                                # Cannot identify this tool call — skip
                                continue

                            buf = self._tc_buffer[buf_key]
                            if name:
                                buf["name"] = name
                            if args:
                                buf["arguments"] = args

                            # Only emit when we have BOTH name AND non-empty arguments
                            # Also verify arguments are valid JSON to avoid sending malformed data
                            if buf["name"] and buf["arguments"]:
                                try:
                                    json.loads(buf["arguments"])
                                except json.JSONDecodeError:
                                    logger.warning(
                                        "[chat] Tool call {} has malformed arguments ({} chars), waiting for more data",
                                        buf["name"],
                                        len(buf["arguments"]),
                                    )
                                    continue
                                # Complete — emit and execute
                                tc_complete = buf
                                tc_id_complete = (
                                    tc_id or f"idx:{tc.get('index')}:{buf['name']}"
                                )
                                name_complete = buf["name"]
                                args_complete = buf["arguments"]
                                # Preserve thought_signature from Gemini's tool call
                                extra_content = buf.get("extra_content") or {}

                                logger.info(
                                    "[chat] LLM requests tool call: name={}",
                                    name_complete,
                                )
                                yield f"data: {json.dumps({'type': 'tool_call', 'tool': name_complete, 'arguments': args_complete})}\n\n"

                                logger.debug(
                                    "[chat] Executing tool={} user_id={} args={}",
                                    name_complete,
                                    cmd.user_id,
                                    args_complete,
                                )
                                result = await self._tool_executor.execute(
                                    tool_name=name_complete,
                                    arguments=args_complete,
                                    user_id=cmd.user_id,
                                    conversation_id=conv_id,
                                )
                                logger.info(
                                    "[chat] Tool={} result_keys={}",
                                    name_complete,
                                    list(result.keys()),
                                )
                                if name_complete in ("search_knowledge_base", "web_search"):
                                    evidence_tools_called = True
                                    if self._tool_result_has_evidence(name_complete, result):
                                        evidence_has_hits = True
                                yield f"data: {json.dumps({'type': 'tool_result', 'tool': name_complete, 'result': result})}\n\n"

                                tool_calls_this_round.append(
                                    {
                                        "id": tc_id_complete,
                                        "type": "function",
                                        "function": {
                                            "name": name_complete,
                                            "arguments": args_complete,
                                        },
                                        "extra_content": extra_content,
                                    }
                                )
                                messages.append(
                                    {
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": [
                                            {
                                                "id": tc_id_complete,
                                                "type": "function",
                                                "function": {
                                                    "name": name_complete,
                                                    "arguments": args_complete,
                                                },
                                                "extra_content": extra_content,
                                            }
                                        ],
                                    }
                                )
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tc_id_complete,
                                        "content": json.dumps(result),
                                    }
                                )

                                # Remove from buffer so we don't re-process
                                self._tc_buffer.pop(buf_key, None)

                        # End of response
                        finish_reason = delta.get("finish_reason") or msg.get(
                            "finish_reason"
                        )
                        if (
                            finish_reason == "stop"
                            and not tool_calls_this_round
                            and not done_sent
                        ):
                            msg_id_for_done = (
                                str(assistant_msg_id) if assistant_msg_id else ""
                            )
                            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': msg_id_for_done})}\n\n"
                            done_emitted = True
                            done_sent = True

                # Accumulate text produced in this round
                if round_text_parts:
                    assistant_text_parts.extend(round_text_parts)

                logger.debug(
                    "[chat] LLM stream round complete: conv_id={} tool_calls={}",
                    conv_id,
                    len(tool_calls_this_round),
                )

                # If no tool calls were made this round, the LLM gave a final text
                # response — exit the agentic loop. Otherwise continue to let the
                # LLM process tool results in the next round.
                if tool_calls_this_round and evidence_tools_called and not evidence_has_hits:
                    logger.info(
                        "[chat] No evidence found after evidence tool calls; applying fallback reply: conv_id={}",
                        conv_id,
                    )
                    assistant_text_parts.append(_EVIDENCE_FALLBACK_TEXT)
                    yield f"data: {json.dumps({'type': 'text', 'content': _EVIDENCE_FALLBACK_TEXT})}\n\n"
                    if not done_sent:
                        msg_id_for_done = (
                            str(assistant_msg_id) if assistant_msg_id else ""
                        )
                        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': msg_id_for_done})}\n\n"
                        done_sent = True
                    break

                if not tool_calls_this_round:
                    # Guarantee a done event even if the API omitted finish_reason
                    if not done_emitted and not done_sent:
                        msg_id_for_done = (
                            str(assistant_msg_id) if assistant_msg_id else ""
                        )
                        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': msg_id_for_done})}\n\n"
                        done_sent = True
                    break
            else:
                logger.warning(
                    "[chat] Agentic loop max rounds reached: conv_id={}", conv_id
                )
                yield f"data: {json.dumps({'type': 'error', 'code': 503, 'message': 'Agentic loop exceeded max rounds.'})}\n\n"
                if not done_sent:
                    msg_id_for_done = str(assistant_msg_id)
                    yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': msg_id_for_done})}\n\n"
                return

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[chat] LLM HTTP error: conv_id={} status={}",
                conv_id,
                exc.response.status_code,
            )
            yield f"data: {json.dumps({'type': 'error', 'code': exc.response.status_code, 'message': f'LLM API error: {exc.response.status_code}'})}\n\n"
            if not done_sent:
                msg_id_for_done = str(assistant_msg_id)
                yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': msg_id_for_done})}\n\n"
            return

        # 3. Persist full assistant reply after streaming completes
        if assistant_text_parts:
            full_reply = "".join(assistant_text_parts)
            logger.debug(
                "[chat] Assistant reply saved: conv_id={} chars={}",
                conv_id,
                len(full_reply),
            )
            await self._chat_repo.save_message(
                Message(
                    id=MessageId(assistant_msg_id),
                    conversation_id=conv_id_vo,
                    role=MessageRole.ASSISTANT,
                    content=full_reply,
                )
            )

    async def _build_personalized_rag_context(
        self,
        *,
        user_id: str,
        user_message: str,
        conversation_id: str | None = None,
    ) -> str | None:
        """Build a hidden, resume-aware context message for this chat turn.

        Flow:
        1) get_user_profile
        2) get_user_resumes (all)
        3) compose a mixed query from message + profile + primary/latest resume
        4) search_knowledge_base once (top_k=3)
        5) convert hits to a short system context message

        Any failure should degrade gracefully and return None.
        """
        try:
            profile_result = await self._tool_executor.execute(
                tool_name="get_user_profile",
                arguments="{}",
                user_id=user_id,
                conversation_id=conversation_id,
            )
            resumes_result = await self._tool_executor.execute(
                tool_name="get_user_resumes",
                arguments=json.dumps({"resume_ids": []}, ensure_ascii=False),
                user_id=user_id,
                conversation_id=conversation_id,
            )
            selected_resume = self._select_resume_for_personalization(
                resumes_result.get("resumes")
                if isinstance(resumes_result, dict)
                else None
            )
            mixed_query = self._build_personalization_query(
                user_message=user_message,
                profile=profile_result if isinstance(profile_result, dict) else {},
                resume=selected_resume,
            )
            if not mixed_query:
                return None

            rag_result = await self._tool_executor.execute(
                tool_name="search_knowledge_base",
                arguments=json.dumps(
                    {
                        "query": mixed_query,
                        "top_k": _PERSONALIZATION_TOP_K,
                        "category": None,
                    },
                    ensure_ascii=False,
                ),
                user_id=user_id,
                conversation_id=conversation_id,
            )
            context = self._format_personalized_context(
                mixed_query=mixed_query,
                rag_result=rag_result if isinstance(rag_result, dict) else {},
            )
            if context:
                logger.debug(
                    "[chat] Personalized context prepared: user_id={} query_chars={}",
                    user_id,
                    len(mixed_query),
                )
            return context
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[chat] Personalized context skipped due to preflight error: user_id={} err={}",
                user_id,
                exc,
            )
            return None

    @staticmethod
    def _select_resume_for_personalization(
        resumes: Any,
    ) -> dict[str, Any] | None:
        """Select primary resume first; fallback to first resume item."""
        if not isinstance(resumes, list):
            return None
        normalized = [item for item in resumes if isinstance(item, dict)]
        if not normalized:
            return None
        for item in normalized:
            if bool(item.get("is_primary")):
                return item
        return normalized[0]

    @staticmethod
    def _normalize_segment(raw: Any) -> str:
        if raw is None:
            return ""
        return " ".join(str(raw).split()).strip()

    def _build_personalization_query(
        self,
        *,
        user_message: str,
        profile: dict[str, Any],
        resume: dict[str, Any] | None,
    ) -> str:
        """Compose `message + career + tags + resume` mixed query."""
        segments: list[str] = []

        def _append_segment(value: Any) -> None:
            normalized = self._normalize_segment(value)
            if normalized:
                segments.append(normalized)

        _append_segment(user_message)

        _append_segment(profile.get("career"))
        tags = profile.get("tags")
        if isinstance(tags, list):
            _append_segment(
                " ".join(
                    self._normalize_segment(tag)
                    for tag in tags
                    if self._normalize_segment(tag)
                )
            )

        if isinstance(resume, dict):
            _append_segment(resume.get("title"))
            _append_segment(resume.get("summary"))

            skills = resume.get("skills")
            if isinstance(skills, list):
                skill_names: list[str] = []
                for skill in skills:
                    if not isinstance(skill, dict):
                        continue
                    name = self._normalize_segment(skill.get("name"))
                    if name:
                        skill_names.append(name)
                    if len(skill_names) >= _PERSONALIZATION_MAX_SKILLS:
                        break
                if skill_names:
                    _append_segment(" ".join(skill_names))

            work_experiences = resume.get("work_experiences")
            if isinstance(work_experiences, list):
                positions: list[str] = []
                for exp in work_experiences:
                    if not isinstance(exp, dict):
                        continue
                    pos = self._normalize_segment(exp.get("position"))
                    if pos:
                        positions.append(pos)
                    if len(positions) >= _PERSONALIZATION_MAX_POSITIONS:
                        break
                if positions:
                    _append_segment(" ".join(positions))

        deduped: list[str] = []
        seen: set[str] = set()
        for seg in segments:
            key = seg.casefold()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(seg)

        mixed = " | ".join(deduped).strip()
        if len(mixed) > _PERSONALIZATION_MAX_QUERY_CHARS:
            mixed = mixed[:_PERSONALIZATION_MAX_QUERY_CHARS].rstrip()
        return mixed

    @staticmethod
    def _tool_result_has_evidence(tool_name: str, result: Any) -> bool:
        if not isinstance(result, dict):
            return False
        if tool_name == "search_knowledge_base":
            hits = result.get("hits")
            return isinstance(hits, list) and len(hits) > 0
        if tool_name == "web_search":
            results = result.get("results")
            return isinstance(results, list) and len(results) > 0
        return False

    def _format_personalized_context(
        self,
        *,
        mixed_query: str,
        rag_result: dict[str, Any],
    ) -> str | None:
        """Turn RAG hits into a short hidden system context."""
        if rag_result.get("error"):
            return None
        hits = rag_result.get("hits")
        if not isinstance(hits, list) or not hits:
            return None

        lines: list[str] = [
            "以下為系統依照使用者履歷與背景整理的個人化參考，僅在有助於回答時優先採用。",
            f"個人化檢索查詢：{mixed_query}",
            "個人化知識命中：",
        ]
        for idx, hit in enumerate(hits[:_PERSONALIZATION_TOP_K], start=1):
            if not isinstance(hit, dict):
                continue
            filename = self._normalize_segment(hit.get("filename")) or "未知來源"
            title = self._normalize_segment(hit.get("title")) or filename
            snippet = self._normalize_segment(hit.get("snippet"))
            if len(snippet) > _PERSONALIZATION_MAX_SNIPPET_CHARS:
                snippet = f"{snippet[:_PERSONALIZATION_MAX_SNIPPET_CHARS].rstrip()}..."
            lines.append(
                f"{idx}. {title}（來源：{filename}）重點：{snippet or '（無摘要）'}"
            )
        if len(lines) <= 3:
            return None
        return "\n".join(lines)

    # ── Conversation management ──────────────────────────────────────────────

    async def update_conversation(self, cmd: UpdateConversationCommand) -> None:
        """Update a conversation's title. Raises 404/403 if not found or not owned."""
        conv_id = ConversationId.from_str(cmd.conversation_id)
        user_id = ChatUserId.from_str(cmd.user_id)
        conversation = await self._chat_repo.find_conversation_by_id(conv_id)
        if conversation is None:
            raise ResourceNotFoundException(
                f"Conversation '{cmd.conversation_id}' not found.",
                code="CONVERSATION_NOT_FOUND",
            )
        if str(conversation.user_id().value) != cmd.user_id:
            raise ForbiddenException(
                "You are not allowed to modify this conversation.",
                code="CONVERSATION_FORBIDDEN",
            )
        now = datetime.now(tz=timezone.utc)
        conversation.update_title(cmd.title, now)
        await self._chat_repo.save_conversation(conversation)
        logger.debug(
            "[chat] Conversation title updated: conv_id={} title={}",
            cmd.conversation_id,
            cmd.title,
        )

    async def delete_conversation(self, cmd: DeleteConversationCommand) -> None:
        """Delete a conversation and all its messages. Raises 404 if not found or not owned."""
        conv_id = ConversationId.from_str(cmd.conversation_id)
        user_id = ChatUserId.from_str(cmd.user_id)
        conversation = await self._chat_repo.find_conversation_by_id(conv_id)
        if conversation is None:
            raise ResourceNotFoundException(
                f"Conversation '{cmd.conversation_id}' not found.",
                code="CONVERSATION_NOT_FOUND",
            )
        if str(conversation.user_id().value) != cmd.user_id:
            raise ForbiddenException(
                "You are not allowed to delete this conversation.",
                code="CONVERSATION_FORBIDDEN",
            )
        deleted = await self._chat_repo.delete_conversation(conv_id, user_id)
        if not deleted:
            raise ResourceNotFoundException(
                f"Conversation '{cmd.conversation_id}' not found.",
                code="CONVERSATION_NOT_FOUND",
            )
        logger.info(
            "[chat] Conversation deleted: conv_id={} user_id={}",
            cmd.conversation_id,
            cmd.user_id,
        )

    # ── Message management ─────────────────────────────────────────────────────

    async def update_message(self, cmd: UpdateMessageCommand) -> int:
        """Edit a message and cascade-delete all messages after it.

        Returns the count of messages deleted in the cascade truncation.
        Raises 404/403 if conversation or message not found or not owned.
        """
        conv_id = ConversationId.from_str(cmd.conversation_id)
        user_id = ChatUserId.from_str(cmd.user_id)
        conversation = await self._chat_repo.find_conversation_by_id(conv_id)
        if conversation is None:
            raise ResourceNotFoundException(
                f"Conversation '{cmd.conversation_id}' not found.",
                code="CONVERSATION_NOT_FOUND",
            )
        if str(conversation.user_id().value) != cmd.user_id:
            raise ForbiddenException(
                "You are not allowed to modify this conversation.",
                code="CONVERSATION_FORBIDDEN",
            )
        # Find the target message in this conversation
        messages = await self._chat_repo.find_messages_by_conversation(conv_id, limit=1)
        target_msg_id = MessageId.from_str(cmd.message_id)
        # Locate the message among the conversation's messages
        all_messages = await self._chat_repo.find_messages_by_conversation(
            conv_id, limit=9999
        )
        target_idx = None
        for i, m in enumerate(all_messages):
            if str(m.id().value) == cmd.message_id:
                target_idx = i
                break
        if target_idx is None:
            raise ResourceNotFoundException(
                f"Message '{cmd.message_id}' not found in conversation.",
                code="MESSAGE_NOT_FOUND",
            )
        target_msg = all_messages[target_idx]
        # Update content via domain method
        target_msg.update_content(cmd.content)
        await self._chat_repo.save_message(target_msg)
        # Truncate messages after the target (exclusive)
        deleted_count = await self._chat_repo.truncate_messages_after(
            conv_id, user_id, target_msg_id
        )
        logger.info(
            "[chat] Message edit cascade: conv_id={} msg_id={} truncated_count={}",
            cmd.conversation_id,
            cmd.message_id,
            deleted_count,
        )
        return deleted_count

    async def delete_message(self, cmd: DeleteMessageCommand) -> int:
        """Delete a message and cascade-delete all messages after it.

        Returns the count of messages deleted in the cascade truncation (including the target).
        Raises 404/403 if conversation or message not found or not owned.
        """
        conv_id = ConversationId.from_str(cmd.conversation_id)
        user_id = ChatUserId.from_str(cmd.user_id)
        conversation = await self._chat_repo.find_conversation_by_id(conv_id)
        if conversation is None:
            raise ResourceNotFoundException(
                f"Conversation '{cmd.conversation_id}' not found.",
                code="CONVERSATION_NOT_FOUND",
            )
        if str(conversation.user_id().value) != cmd.user_id:
            raise ForbiddenException(
                "You are not allowed to modify this conversation.",
                code="CONVERSATION_FORBIDDEN",
            )
        # Verify the message belongs to this conversation
        all_messages = await self._chat_repo.find_messages_by_conversation(
            conv_id, limit=9999
        )
        target_idx = None
        for i, m in enumerate(all_messages):
            if str(m.id().value) == cmd.message_id:
                target_idx = i
                break
        if target_idx is None:
            raise ResourceNotFoundException(
                f"Message '{cmd.message_id}' not found in conversation.",
                code="MESSAGE_NOT_FOUND",
            )
        target_msg_id = MessageId.from_str(cmd.message_id)
        # First cascade-delete all messages newer than the target
        deleted_count = await self._chat_repo.truncate_messages_after(
            conv_id, user_id, target_msg_id
        )
        # Then delete the target message itself (truncate_messages_after uses strictly-after, so the
        # target is intentionally excluded from that call)
        await self._chat_repo.delete_message_by_id(target_msg_id, conv_id)
        total_deleted = deleted_count + 1
        logger.info(
            "[chat] Message delete cascade: conv_id={} msg_id={} total_deleted={}",
            cmd.conversation_id,
            cmd.message_id,
            total_deleted,
        )
        return total_deleted
