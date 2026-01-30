import { createContext, useContext } from "react";

interface SidebarLayoutContextValue {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

const SidebarLayoutContext = createContext<SidebarLayoutContextValue | null>(
  null,
);

export function SidebarLayoutProvider({
  value,
  children,
}: {
  value: SidebarLayoutContextValue;
  children: React.ReactNode;
}) {
  return (
    <SidebarLayoutContext.Provider value={value}>
      {children}
    </SidebarLayoutContext.Provider>
  );
}

export function useSidebarLayout() {
  return useContext(SidebarLayoutContext);
}

