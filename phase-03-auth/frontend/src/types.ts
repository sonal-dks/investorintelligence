export type UserRole = "investor" | "admin";

export type UserProfile = {
  id: string;
  user_id: string;
  email: string | null;
  display_name: string | null;
  role: UserRole;
  first_login_complete: boolean;
  created_at: string;
  updated_at: string;
};
