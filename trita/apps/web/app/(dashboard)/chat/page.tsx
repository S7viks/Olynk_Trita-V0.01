import { ChatPanel } from "@/components/chat-panel";
import { PageHeader } from "@/components/ui/page-header";

export default function ChatPage() {
  return (
    <section>
      <PageHeader
        title="Inventory chat"
        description="Grounded answers from your tenant graph only (F-CHAT-001/002). Refuses non-inventory topics. Does not compute reorder qty or ₹ impact (VA-03)."
      />
      <ChatPanel />
    </section>
  );
}
