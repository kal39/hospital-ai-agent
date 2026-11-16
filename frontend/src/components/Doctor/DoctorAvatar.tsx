import { useState } from "react";

interface DoctorAvatarProps {
  doctorId: string;
  doctorName: string;
  className?: string;
}

/**
 * Shared doctor portrait.
 *
 * Expected local image:
 * /public/doctor-photos/{doctorId}.webp
 *
 * If the portrait is missing or cannot load, initials are displayed.
 */
export default function DoctorAvatar({
  doctorId,
  doctorName,
  className = "",
}: DoctorAvatarProps) {
  const [imageFailed, setImageFailed] = useState(false);

  const initials = doctorName
    .replace(/^Dr\.?\s*/i, "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");

  const imagePath = `/doctor-photos/${doctorId}.webp`;

  return (
    <div
      className={`doctor-avatar ${className}`.trim()}
      aria-hidden="true"
    >
      {!imageFailed ? (
        <img
          src={imagePath}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  );
}
