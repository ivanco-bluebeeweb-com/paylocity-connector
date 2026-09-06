"""Panel UI for Paylocity Connector following UI_INTERFACE_STANDARD.md and AUTH_AND_CREDENTIALS_STANDARD.md."""
from __future__ import annotations
from imperal_sdk import ui
from app import ext

def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings",
        variant="secondary",
        size="sm",
        icon="settings",
        on_click=ui.Call("__panel__paylocity_settings")
    )

def _help_modal() -> ui.UINode:
    return ui.Modal(
        trigger=ui.Button("How do I connect Paylocity?", variant="ghost", size="sm"),
        title="Connecting Paylocity",
        children=[
            ui.Text(
                "1. Sign in to your Paylocity portal at access.paylocity.com.\n"
                "2. Your Company ID (e.g. 9-digit or alphanumeric) is visible in the top navigation or company setup.\n"
                "3. In Web Services / API Access settings, request or generate an API Bearer Token.\n"
                "4. Enter your API Token and Company ID above and click Connect Paylocity.",
                variant="body"
            )
        ]
    )

@ext.panel("paylocity_sidebar", slot="left")
async def paylocity_sidebar(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(
        direction="v",
        gap=3,
        align="stretch",
        children=[
            ui.Text("Paylocity", variant="heading"),
            ui.Text("Manage employees, payroll runs, departments, time-off and direct deposits via Paylocity Web Services API.", variant="caption"),
            ui.Divider(),
            ui.Form(
                submit_label="Connect Paylocity",
                action=ui.Call("connect_paylocity"),
                children=[
                    ui.Stack(
                        direction="v",
                        gap=2,
                        align="stretch",
                        children=[
                            ui.Text("Connection Label", variant="caption"),
                            ui.Input(
                                param_name="label",
                                placeholder="e.g. Acme Paylocity"
                            ),
                            ui.Text("API Bearer Token", variant="caption"),
                            ui.Input(
                                param_name="api_token",
                                placeholder="Paste Paylocity Web Services API Token"
                            ),
                            ui.Text("Company ID", variant="caption"),
                            ui.Input(
                                param_name="company_id",
                                placeholder="e.g. 12345"
                            ),
                            ui.Text("Custom Base URL (Optional)", variant="caption"),
                            ui.Input(
                                param_name="base_url",
                                placeholder="https://api.paylocity.com/api/v2"
                            )
                        ]
                    )
                ]
            ),
            ui.Divider(),
            ui.Stack(
                direction="v",
                gap=2,
                align="stretch",
                children=[
                    _help_modal(),
                    _settings_button()
                ]
            )
        ]
    )
