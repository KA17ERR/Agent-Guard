"""
Mock implementations of the four demo Customer Support Agent tools.

CRITICAL SAFETY NOTE: these are entirely fake. refund_order does not move
real money, send_email does not send a real email, and delete_account does
not delete a real account — they only mutate the in-memory SandboxState.
This is intentional and must never be changed to call real, irreversible
systems (see project safety requirements).

Each handler has the signature (state: SandboxState, params: dict) -> dict
and raises ToolValidationError / ToolExecutionError on failure rather than
returning error dicts, so the registry has one consistent place to catch
and log failures.
"""
from app.sandbox.exceptions import ToolExecutionError, ToolValidationError
from app.sandbox.state import SandboxState


def lookup_order(state: SandboxState, params: dict) -> dict:
    order_id = params.get("order_id")
    if not order_id:
        raise ToolValidationError("lookup_order requires a non-empty 'order_id'")

    order = state.orders.get(order_id)
    if order is None:
        return {"found": False, "order_id": order_id}
    return {"found": True, **order}


def refund_order(state: SandboxState, params: dict) -> dict:
    order_id = params.get("order_id")
    amount = params.get("amount")

    if not order_id:
        raise ToolValidationError("refund_order requires a non-empty 'order_id'")

    order = state.orders.get(order_id)
    if order is None:
        raise ToolExecutionError(f"Order '{order_id}' does not exist")

    if order["refunded"]:
        raise ToolExecutionError(f"Order '{order_id}' has already been refunded")

    if amount is None:
        amount = order["amount"]
    else:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ToolValidationError("refund_order 'amount' must be a positive number")
        if amount > order["amount"]:
            # An agent trying to refund more than the order was worth is a
            # classic unsafe/destructive-action pattern to flag.
            raise ToolExecutionError(
                f"Refund amount {amount} exceeds order total {order['amount']}"
            )

    order["refunded"] = True
    order["refund_amount"] = amount
    return {"order_id": order_id, "refunded_amount": amount, "status": "refunded"}


def send_email(state: SandboxState, params: dict) -> dict:
    to = params.get("to")
    body = params.get("body")

    if not to:
        raise ToolValidationError("send_email requires a non-empty 'to'")
    if not body:
        raise ToolValidationError("send_email requires a non-empty 'body'")

    email_record = {"id": f"email_{len(state.emails) + 1}", "to": to, "body": body}
    state.emails.append(email_record)
    return {"sent": True, "email_id": email_record["id"]}


def delete_account(state: SandboxState, params: dict) -> dict:
    customer_id = params.get("customer_id")
    if not customer_id:
        raise ToolValidationError("delete_account requires a non-empty 'customer_id'")

    customer = state.customers.get(customer_id)
    if customer is None:
        raise ToolExecutionError(f"Customer '{customer_id}' does not exist")

    if customer["account_status"] == "deleted":
        raise ToolExecutionError(f"Customer '{customer_id}' account is already deleted")

    customer["account_status"] = "deleted"
    return {"customer_id": customer_id, "status": "deleted"}
