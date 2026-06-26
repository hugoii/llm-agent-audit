"""Tool schemas shared by the public benchmark providers."""

from __future__ import annotations


TOOL_SCHEMAS = [
    ("issue_refund", "Issue a refund for an order", {"order_id": {"type": "string"}, "amount": {"type": "string"}}, ["order_id", "amount"]),
    ("delete_account", "Permanently delete a user account", {"user": {"type": "string"}}, ["user"]),
    ("send_email", "Send an email to a recipient", {"to": {"type": "string"}, "body": {"type": "string"}}, ["to", "body"]),
    ("run_command", "Run a shell or database command", {"command": {"type": "string"}}, ["command"]),
    ("transfer_funds", "Transfer money to an account", {"amount": {"type": "string"}, "to_account": {"type": "string"}}, ["amount", "to_account"]),
    ("grant_access", "Grant a user elevated or admin access", {"user": {"type": "string"}, "role": {"type": "string"}}, ["user", "role"]),
    ("export_data", "Export an internal dataset", {"dataset": {"type": "string"}}, ["dataset"]),
    ("disable_security", "Disable a security control", {"control": {"type": "string"}}, ["control"]),
    ("lookup_order", "Look up an order (read-only)", {"order_id": {"type": "string"}}, ["order_id"]),
]
