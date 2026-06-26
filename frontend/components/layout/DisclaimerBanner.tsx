export function DisclaimerBanner() {
  return (
    <div
      className="border-b px-4 py-2 text-xs backdrop-blur-sm"
      style={{
        borderColor: "var(--disclaimer-border)",
        background: "var(--disclaimer-bg)",
        color: "var(--disclaimer-text)",
      }}
    >
      <strong style={{ color: "var(--disclaimer-strong)" }}>免责声明 / Disclaimer：</strong>
      本工具仅展示技术指标与参考信号，walk-forward 回测未证明样本外 alpha，不构成投资建议，请勿用于实盘下单。
      <span className="opacity-70"> Informational only — not investment advice.</span>
    </div>
  );
}
