import { useState } from "react";
import { Outlet } from "react-router";
import ThreadsLayout from "../components/layout/ThreadsLayout";
import type { ThreadCategory } from "../components/threads/ThreadsSidebar";

export default function ThreadsRouteLayout() {
  const [activeCategory, setActiveCategory] = useState<ThreadCategory>("all");

  return (
    <ThreadsLayout
      activeCategory={activeCategory}
      onSelectCategory={setActiveCategory}
    >
      <Outlet />
    </ThreadsLayout>
  );
}

