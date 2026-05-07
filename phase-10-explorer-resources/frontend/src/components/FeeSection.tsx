import { useState } from "react";

type FeeItem = {
  category: string;
  description: string;
  typical_range: string | null;
  applicable_to: string | null;
  notes: string | null;
};

type FeeSectionProps = {
  title: string;
  items: FeeItem[];
};

export function FeeSection({ title, items }: FeeSectionProps) {
  const [open, setOpen] = useState(false);
  return (
    <section style={{ border: "1px solid #e5e7eb", borderRadius: 12, marginBottom: 12 }}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        style={{ width: "100%", textAlign: "left", padding: 12, background: "white", border: "none", fontWeight: 600 }}
      >
        {title}
      </button>
      {open && (
        <div style={{ padding: "0 12px 12px" }}>
          {items.map((item, idx) => (
            <div key={`${title}-${idx}`} style={{ borderTop: "1px solid #f3f4f6", paddingTop: 8, marginTop: 8 }}>
              <div style={{ fontWeight: 600 }}>{item.category}</div>
              <div>{item.description}</div>
              <div style={{ color: "#4b5563", fontSize: 13 }}>
                Range: {item.typical_range || "N/A"} | Applies to: {item.applicable_to || "N/A"}
              </div>
              {item.notes ? <div style={{ color: "#4b5563", fontSize: 13 }}>Notes: {item.notes}</div> : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
