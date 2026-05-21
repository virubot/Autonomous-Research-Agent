import { Plus, MessageSquare, PanelLeftClose, PanelLeftOpen, Trash2, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

export type ChatSummary = {
  id: string;
  title: string;
  preview: string;
  updatedAt: string;
};

interface ChatSidebarProps {
  chats: ChatSummary[];
  activeId: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  collapsed: boolean;
  onToggle: () => void;
}

export const ChatSidebar = ({
  chats,
  activeId,
  onSelect,
  onNewChat,
  onDeleteChat,
  collapsed,
  onToggle,
}: ChatSidebarProps) => {
  return (
    <aside
      className={cn(
        "relative z-20 flex h-full flex-col border-r border-white/5 bg-black/40 backdrop-blur-3xl transition-[width] duration-300",
        collapsed ? "w-[68px]" : "w-[280px]"
      )}
    >
      {/* Brand */}
      <div className="flex items-center justify-between gap-2 px-4 pt-5 pb-4">
        <div className={cn("flex items-center gap-3 overflow-hidden", collapsed && "w-full justify-center")}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent shadow-soft">
            <Bot className="h-4 w-4 text-white" strokeWidth={2.5} />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-[14px] font-bold leading-tight tracking-wide text-foreground">Agent <span className="text-primary text-[14px]">Studio</span></p>
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest mt-0.5">Workspace</p>
            </div>
          )}
        </div>
        {!collapsed && (
          <button
            onClick={onToggle}
            className="ring-focus rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          onClick={onToggle}
          className="ring-focus mx-auto mb-2 rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground"
          aria-label="Expand sidebar"
        >
          <PanelLeftOpen className="h-4 w-4" />
        </button>
      )}

      {/* New chat */}
      <div className="px-3">
        <button
          onClick={onNewChat}
          className={cn(
            "ring-focus flex w-full items-center gap-2 rounded-xl bg-white/5 px-3 py-2.5 text-sm font-semibold text-foreground transition-all hover:bg-white/10 active:scale-[0.98]",
            collapsed && "justify-center px-0"
          )}
        >
          <Plus className="h-4 w-4 shrink-0 text-foreground" strokeWidth={2.5} />
          {!collapsed && <span>New workflow</span>}
        </button>
      </div>

      {/* History label */}
      {!collapsed && (
        <div className="mt-6 px-5 pb-2">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
            Recent Workflows
          </p>
        </div>
      )}

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <ul className="space-y-1">
          {chats.map((chat) => {
            const active = chat.id === activeId;
            return (
              <li key={chat.id}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => onSelect(chat.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelect(chat.id);
                    }
                  }}
                  className={cn(
                    "group relative flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                    active
                      ? "bg-primary/20 text-foreground shadow-soft border border-primary/20"
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground border border-transparent",
                    collapsed && "justify-center px-0"
                  )}
                >
                  <MessageSquare
                    className={cn(
                      "h-4 w-4 shrink-0",
                      active ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                    )}
                    strokeWidth={2}
                  />
                  {!collapsed && (
                    <>
                      <div className="min-w-0 flex-1">
                        <p className={cn("truncate text-[13px] font-semibold leading-tight", active ? "text-primary-foreground" : "text-foreground")}>
                          {chat.title}
                        </p>
                        <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                          {chat.preview}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteChat(chat.id);
                        }}
                        className="ring-focus shrink-0 rounded-md p-1.5 text-muted-foreground opacity-0 transition-all hover:bg-destructive/20 hover:text-destructive group-hover:opacity-100 focus:opacity-100"
                        aria-label={`Delete chat ${chat.title}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-white/5 bg-black/20">
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 shadow-[0_0_15px_rgba(52,211,153,0.3)]">
              <span className="text-[12px] font-bold text-black">ON</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-foreground">Agent Runtime</p>
              <p className="truncate text-[11px] text-emerald-400 font-medium">Memory & tools active</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
