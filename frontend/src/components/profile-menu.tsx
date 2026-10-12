"use client";

import { ChevronRightIcon, PackageIcon, UserIcon } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { Order, Profile } from "@/lib/types";

type View = "profile" | "orders" | "order" | null;

type LoadState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };

async function fetchJson<T>(url: string, key: string): Promise<T> {
  const res = await fetch(url);
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
  return body[key] as T;
}

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

const dateFmt = new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" });

const formatDate = (iso: string | null) =>
  iso ? dateFmt.format(new Date(iso)) : "—";


function useLoad<T>(view: View, url: string | null, key: string) {
  const [state, setState] = useState<LoadState<T>>({ status: "idle" });
  const [lastKey, setLastKey] = useState<string | null>(null);

  // Re-fetch whenever the requested URL changes while a view is open.
  const requestKey = view && url ? url : null;
  if (requestKey !== lastKey) {
    setLastKey(requestKey);
    if (requestKey) {
      setState({ status: "loading" });
      fetchJson<T>(requestKey, key).then(
        (data) => setState({ status: "ready", data }),
        (error: Error) => setState({ status: "error", message: error.message }),
      );
    } else {
      setState({ status: "idle" });
    }
  }
  return state;
}

export function ProfileMenu() {
  const [view, setView] = useState<View>(null);
  const [orderId, setOrderId] = useState<string | null>(null);

  const profile = useLoad<Profile>(
    view === "profile" ? view : null,
    view === "profile" ? "/api/profile" : null,
    "user",
  );
  const orders = useLoad<Order[]>(
    view === "orders" ? view : null,
    view === "orders" ? "/api/orders" : null,
    "orders",
  );
  const order = useLoad<Order>(
    view === "order" ? view : null,
    view === "order" && orderId ? `/api/orders/${encodeURIComponent(orderId)}` : null,
    "order",
  );

  const close = () => setView(null);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button variant="ghost" size="icon" className="rounded-full" aria-label="Account menu" />
          }
        >
          <Avatar>
            <AvatarFallback>
              <UserIcon className="size-4" />
            </AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => setView("profile")}>
            <UserIcon /> View profile
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setView("orders")}>
            <PackageIcon /> Orders
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={view === "profile"} onOpenChange={(open) => !open && close()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Profile</DialogTitle>
            <DialogDescription>Your account details.</DialogDescription>
          </DialogHeader>
          {profile.status === "loading" && <p className="text-sm text-muted-foreground">Loading…</p>}
          {profile.status === "error" && <p className="text-sm text-destructive">{profile.message}</p>}
          {profile.status === "ready" && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
              <dt className="text-muted-foreground">Name</dt>
              <dd>{profile.data.name}</dd>
              <dt className="text-muted-foreground">Email</dt>
              <dd>{profile.data.email}</dd>
              <dt className="text-muted-foreground">Phone</dt>
              <dd>{profile.data.phone}</dd>
            </dl>
          )}
        </DialogContent>
      </Dialog>

      <Sheet open={view === "orders"} onOpenChange={(open) => !open && close()}>
        <SheetContent className="w-full sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Orders</SheetTitle>
            <SheetDescription>Select an order to see its details.</SheetDescription>
          </SheetHeader>
          <ScrollArea className="flex-1 px-4 pb-4">
            {orders.status === "loading" && <p className="text-sm text-muted-foreground">Loading…</p>}
            {orders.status === "error" && <p className="text-sm text-destructive">{orders.message}</p>}
            {orders.status === "ready" && orders.data.length === 0 && (
              <p className="text-sm text-muted-foreground">No orders yet.</p>
            )}
            {orders.status === "ready" && (
              <ul className="flex flex-col gap-2">
                {orders.data.map((o) => (
                  <li key={o.orderId}>
                    <button
                      type="button"
                      onClick={() => {
                        setOrderId(o.orderId);
                        setView("order");
                      }}
                      className="flex w-full items-center justify-between gap-3 rounded-lg border p-3 text-left transition-colors hover:bg-accent"
                    >
                      <span className="flex flex-col gap-1">
                        <span className="font-medium">{o.orderId}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(o.orderDate)} · {currency.format(o.totalAmount)}
                        </span>
                      </span>
                      <span className="flex items-center gap-2">
                        <Badge variant={o.status === "delivered" ? "default" : o.status === "cancelled" ? "destructive" : "secondary"}>{o.status}</Badge>
                        <ChevronRightIcon className="size-4 text-muted-foreground" />
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </ScrollArea>
        </SheetContent>
      </Sheet>

      <Dialog open={view === "order"} onOpenChange={(open) => !open && close()}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{orderId ?? "Order"}</DialogTitle>
            <DialogDescription>Order details.</DialogDescription>
          </DialogHeader>
          {order.status === "loading" && <p className="text-sm text-muted-foreground">Loading…</p>}
          {order.status === "error" && <p className="text-sm text-destructive">{order.message}</p>}
          {order.status === "ready" && (
            <div className="flex flex-col gap-4 text-sm">
              <div className="flex items-center justify-between">
                <Badge variant={order.data.status === "delivered" ? "default" : order.data.status === "cancelled" ? "destructive" : "secondary"}>{order.data.status}</Badge>
                <span className="font-medium">{currency.format(order.data.totalAmount)}</span>
              </div>
              <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
                <dt className="text-muted-foreground">Ordered</dt>
                <dd>{formatDate(order.data.orderDate)}</dd>
                <dt className="text-muted-foreground">Expected</dt>
                <dd>{formatDate(order.data.expectedDeliveryDate)}</dd>
                <dt className="text-muted-foreground">Delivered</dt>
                <dd>{formatDate(order.data.deliveryDate)}</dd>
                <dt className="text-muted-foreground">Payment</dt>
                <dd>{order.data.paymentMethod}</dd>
                <dt className="text-muted-foreground">Ship to</dt>
                <dd>{order.data.shippingAddress}</dd>
              </dl>
              <Separator />
              <ul className="flex flex-col gap-2">
                {order.data.items.map((item) => (
                  <li key={item.productId} className="flex items-center justify-between">
                    <span>
                      {item.name} <span className="text-muted-foreground">× {item.quantity}</span>
                    </span>
                    <span>{currency.format(item.unitPrice * item.quantity)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Button variant="outline" onClick={() => setView("orders")}>
            Back to orders
          </Button>
        </DialogContent>
      </Dialog>
    </>
  );
}
