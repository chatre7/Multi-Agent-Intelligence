import { Outlet } from "react-router";
import PageLayout from "../components/layout/PageLayout";

export default function AdminRouteLayout() {
  return (
    <PageLayout>
      <Outlet />
    </PageLayout>
  );
}

