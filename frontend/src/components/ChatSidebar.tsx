import { Plus, MessageSquare, PanelLeftClose, PanelLeftOpen, Trash2, BookOpen } from "lucide-react";
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
        "relative z-20 flex h-full flex-col bg-sidebar-background/40 backdrop-blur-xl transition-[width] duration-300",
        collapsed ? "w-[68px]" : "w-72"
      )}
    >
      {/* Brand */}
      <div className="flex items-center justify-between gap-2 px-4 pt-5 pb-4">
        <div className={cn("flex items-center gap-2.5 overflow-hidden", collapsed && "w-full justify-center")}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <BookOpen className="h-4 w-4" strokeWidth={2.2} />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-[13px] font-semibold leading-tight text-foreground">Research</p>
              <p className="text-[11px] text-muted-foreground">Workspace</p>
            </div>
          )}
        </div>
        {!collapsed && (
          <button
            onClick={onToggle}
            className="ring-focus rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-foreground/[0.06] hover:text-foreground"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          onClick={onToggle}
          className="ring-focus mx-auto mb-2 rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-foreground/[0.06] hover:text-foreground"
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
            "ring-focus flex w-full items-center gap-2 rounded-xl bg-foreground/[0.05] px-3 py-2 text-[13px] font-medium text-foreground transition-colors hover:bg-foreground/[0.09]",
            collapsed && "justify-center px-0"
          )}
        >
          <Plus className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={2.2} />
          {!collapsed && <span>New chat</span>}
        </button>
      </div>

      {/* History label */}
      {!collapsed && (
        <div className="mt-6 px-4 pb-2">
          <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            Chat history
          </p>
        </div>
      )}

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto px-2 pb-4">
        <ul className="space-y-0.5">
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
                    "group relative flex w-full cursor-pointer items-center gap-2 rounded-lg px-2.5 py-2 text-left transition-colors",
                    active
                      ? "bg-foreground/[0.07] text-foreground"
                      : "text-muted-foreground hover:bg-foreground/[0.04] hover:text-foreground",
                    collapsed && "justify-center px-0"
                  )}
                >
                  <MessageSquare
                    className={cn(
                      "h-3.5 w-3.5 shrink-0",
                      active ? "text-primary" : "text-muted-foreground"
                    )}
                    strokeWidth={2}
                  />
                  {!collapsed && (
                    <>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-[13px] font-medium leading-tight text-foreground">
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
                        className="ring-focus shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-all hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100 focus:opacity-100"
                        aria-label={`Delete chat ${chat.title}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
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
        <div className="p-3">
          <div className="flex items-center gap-2.5 rounded-lg px-2 py-1.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-foreground/[0.08] text-[11px] font-medium text-foreground">
              R
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[12px] font-medium text-foreground">Researcher</p>
              <p className="truncate text-[10px] text-muted-foreground">Pro plan</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
