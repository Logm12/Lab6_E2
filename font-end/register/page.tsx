"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useActionState, useEffect, useState } from "react";
import { AuthForm } from "@/components/auth-form";
import { SubmitButton } from "@/components/submit-button";
import { toast } from "@/components/toast";
import { type RegisterActionState, register } from "../actions";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Page() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [isSuccessful, setIsSuccessful] = useState(false);

  const [state, formAction] = useActionState<RegisterActionState, FormData>(
    register,
    {
      status: "idle",
    }
  );

  const { update: updateSession } = useSession();

  // biome-ignore lint/correctness/useExhaustiveDependencies: router and updateSession are stable refs
  useEffect(() => {
    if (state.status === "user_exists") {
      toast({ type: "error", description: "Tài khoản đã tồn tại!" });
    } else if (state.status === "failed") {
      toast({ type: "error", description: "Tạo tài khoản thất bại!" });
    } else if (state.status === "invalid_data") {
      toast({
        type: "error",
        description: "Thông tin không hợp lệ!",
      });
    } else if (state.status === "password_mismatch") {
      toast({
        type: "error",
        description: "Mật khẩu nhập lại không trùng khớp!",
      });
    } else if (state.status === "weak_password") {
      toast({
        type: "error",
        description:
          "Mật khẩu yếu: tối thiểu 8 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt.",
      });
    } else if (state.status === "success") {
      toast({ type: "success", description: "Tạo tài khoản thành công!" });

      setIsSuccessful(true);
      updateSession();
      router.refresh();
    }
  }, [state.status]);

  const handleSubmit = (formData: FormData) => {
    setEmail(formData.get("email") as string);
    formAction(formData);
  };

  return (
    <div className="flex h-dvh w-screen items-start justify-center bg-background pt-12 md:items-center md:pt-0">
      <div className="flex w-full max-w-md flex-col gap-12 overflow-hidden rounded-2xl">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <h3 className="font-semibold text-xl dark:text-zinc-50">Đăng ký</h3>
          <p className="text-gray-500 text-sm dark:text-zinc-400">
            Tạo tài khoản với email và mật khẩu của bạn
          </p>
        </div>
        <AuthForm action={handleSubmit} defaultEmail={email}>
          <div className="text-xs text-muted-foreground">
            Mật khẩu cần tối thiểu 8 ký tự, bao gồm chữ hoa (A–Z), chữ thường (a–z), số (0–9), và ký tự đặc biệt (ví dụ: !@#$%^&*).
          </div>
          <div className="flex flex-col gap-2">
            <Label
              className="font-normal text-zinc-600 dark:text-zinc-400"
              htmlFor="passwordConfirm"
            >
              Nhập lại mật khẩu
            </Label>

            <Input
              className="bg-muted text-md md:text-sm"
              id="passwordConfirm"
              name="passwordConfirm"
              required
              type="password"
            />
          </div>
          <SubmitButton isSuccessful={isSuccessful}>Đăng ký</SubmitButton>
          <p className="mt-4 text-center text-gray-600 text-sm dark:text-zinc-400">
            {"Đã có tài khoản? "}
            <Link
              className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
              href="/login"
            >
              Đăng nhập
            </Link>
            {" để tiếp tục."}
          </p>
        </AuthForm>
      </div>
    </div>
  );
}
