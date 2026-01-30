import { Outlet } from "react-router";
import PageLayout from "../components/layout/PageLayout";

export default function HomeRouteLayout() {
  return (
    <PageLayout>
      <Outlet />
    </PageLayout>
  );
}

