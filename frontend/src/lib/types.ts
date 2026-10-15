export type Profile = {
  userId: string;
  name: string;
  email: string;
  phone: string;
};

export type OrderItem = {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
};

export type Order = {
  orderId: number;
  orderDate: string | null;
  status: string;
  items: OrderItem[];
  shippingAddress: string;
  paymentMethod: string;
  totalAmount: number;
  expectedDeliveryDate: string | null;
  deliveryDate: string | null;
};
