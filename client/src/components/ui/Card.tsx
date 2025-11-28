import React from "react";

type DivProps = React.HTMLAttributes<HTMLDivElement>;
interface CardProps extends Omit<DivProps, "title"> {
  title?: React.ReactNode;
}

const Card: React.FC<CardProps> = ({
  title,
  className = "",
  children,
  ...rest
}) => (
  <div
    className={["card fade-in", className].filter(Boolean).join(" ")}
    {...rest}
  >
    {title && (typeof title === "string" ? <h3>{title}</h3> : title)}
    {children}
  </div>
);

export default Card;
