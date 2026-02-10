import Router from "@/components/Router";

export function generateStaticParams() {
  return [{ path: [] }];
}

export default function CatchAllPage() {
  return <Router />;
}
