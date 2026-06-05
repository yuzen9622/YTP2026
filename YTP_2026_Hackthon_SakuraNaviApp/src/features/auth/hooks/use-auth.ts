import { useMutation } from "@tanstack/react-query";
import {
  forgotPassword,
  login,
  register,
  type AuthResponse,
  type LoginPayload,
  type RegisterPayload,
} from "../api/auth-api";

export function useLoginMutation() {
  return useMutation<AuthResponse, Error, LoginPayload>({
    mutationFn: (payload) => login(payload),
  });
}

export function useRegisterMutation() {
  return useMutation<AuthResponse, Error, RegisterPayload>({
    mutationFn: (payload) => register(payload),
  });
}

export function useForgotPasswordMutation() {
  return useMutation<void, Error, string>({
    mutationFn: (email) => forgotPassword(email),
  });
}
