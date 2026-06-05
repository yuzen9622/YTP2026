export interface LoginPayload {
  account: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  account: string;
}