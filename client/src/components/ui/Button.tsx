import React from "react";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      loading = false,
      disabled,
      className = "",
      children,
      ...rest
    },
    ref
  ) => {
    const cls = [variant === "secondary" ? "btn-secondary" : "", className]
      .filter(Boolean)
      .join(" ");
    return (
      <button
        ref={ref}
        className={cls}
        disabled={disabled || loading}
        {...rest}
      >
        {loading ? "..." : children}
      </button>
    );
  }
);

Button.displayName = "Button";
export default Button;
