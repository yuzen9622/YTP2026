import { useState } from "react";
import { ChangePasswordPayload } from "../types";
import { changePassword } from "../api/user-profile-api";
export default function useEditAuth() {
  const [changePasswordPayload, setChangePasswordPayload] =
    useState<ChangePasswordPayload>({
      current_password: "",
      new_password: "",
    });
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handleChangePasswordPayload = (
    field: keyof ChangePasswordPayload,
    value: string,
  ) => {
    setChangePasswordPayload((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleChangePassword = async () => {
    if (isChangingPassword) {
      return;
    }
    setIsChangingPassword(true);
    await changePassword(changePasswordPayload);
    setIsChangingPassword(false);
  };

  return {
    changePasswordPayload,
    isChangingPassword,
    handleChangePasswordPayload,
    handleChangePassword,
  };
}
