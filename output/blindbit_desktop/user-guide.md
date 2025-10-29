# BlindBit Desktop User Guide

> **Last Updated:** 2025-10-29

Step-by-step guide to setting up and using BlindBit Desktop wallet

---

## Table of Contents

- [Building from Source](#building-from-source)
- [Initial Wallet Setup](#initial-wallet-setup)
- [Using BlindBit Desktop](#using-blindbit-desktop)
- [Sending Transactions](#sending-transactions)
- [Receiving Transactions](#receiving-transactions)
- [Troubleshooting](#troubleshooting)

---

## Building from Source

**Source Code:** https://github.com/setavenger/blindbit-desktop

Instructions for compiling BlindBit Desktop from [source](https://github.com/setavenger/blindbit-desktop?tab=readme-ov-file#prerequisites)
Quick Start
1. Verify Go version 1.24 or later
```
go version
```
2. Compile blindbit-desktop
```
cd blindbit-desktop
git checkout -B alpha origin/alpha
go build -o blindbit-desktop ./cmd/blindbit-desktop
./blindbit-desktop
```

---

 ***
## Initial Wallet Setup

This workflow demonstrates how to recover a silent payments wallet from seed phrase

#### Import Existing Wallet

Select "Import Existing Wallet" to restore wallet from seed phrase

<img src="screenshots/setup_import_existing_wallet.png" alt="Import Existing Wallet" style="max-height: 500px;">



---

#### Finalize Import Wallet

- Enter seed phrase
- Select "Import Wallet"

<img src="screenshots/setup_finalize_import_wallet.png" alt="Finalize Import Wallet" style="max-height: 500px;">


**Note:**
> 12 or 24 word mnemonic supported

---

#### Make Network Selection

- Choose "mainnet" for production use
- Select "Continue" to confirm network

<img src="screenshots/setup_make_network_selection.png" alt="Make Network Selection" style="max-height: 500px;">



---

#### Finalize Wallet Setup

- Choose a "block height" to capture any previous silent payment transactions for this wallet
- Select "Save & Continue" to complete setup and start scanning for transactions

<img src="screenshots/setup_finalize_wallet_setup.png" alt="Finalize Wallet Setup" style="max-height: 500px;">


**Note:**
> wallet.dat is stored in ~/.blindbit-desktop by default
> 
> **Warning:** key material in this file is not encrypted at this time
> 

---

#### Scanning

Monitor "Scanning Status" on this view

<img src="screenshots/setup_scanning.png" alt="Scanning" style="max-height: 500px;">



---



 ***
## Using BlindBit Desktop

Overview of wallet and navigation

#### Scanning

View blockchain scanning progress

<img src="screenshots/overview_scanning.png" alt="Scanning" style="max-height: 500px;">


**Note:**
> "Current Scan Height": \# will match "Chain Tip" when sync is complete
> 
> **Rescan Button**: only use this button after changing "birth height" in settings or testing
> 

---

#### UTXOs

View wallet balance and unspent transaction outputs

<img src="screenshots/overview_utxos.png" alt="UTXOs" style="max-height: 500px;">


**Note:**
> Toggle the "Show only unspent UTXOs" to view spent too
> 

---

#### Send

Send bitcoin to other wallets

<img src="screenshots/overview_send.png" alt="Send" style="max-height: 500px;">


**Note:**
> Fee Rate must be greater than or equal to 1 sat/vB
> 

---

#### Receive

Generate addresses to receive payments

<img src="screenshots/overview_receive.png" alt="Receive" style="max-height: 500px;">



---

#### Transactions

View transaction history

<img src="screenshots/overview_transactions.png" alt="Transactions" style="max-height: 500px;">


**Note:**
> received transactions will only appear once the transaction is confirmed in a block
> 
> spending transactions will appear immediately
> 
> fees will only appear if spent from this wallet - not available after recovery
> 

---

#### Settings

Modify wallet settings and configuration

<img src="screenshots/overview_settings.png" alt="Settings" style="max-height: 500px;">


**Note:**
> restart may be required after applying new settings

---



 ***
## Sending Transactions

Highlight the basics of sending a payment from blindbit-desktop

#### Enter Recipient Information

- Enter a recipient address, the amount to send, fee rate
- Select "Send Transaction" to view details

<img src="screenshots/sending_enter_recipient_information.png" alt="Enter Recipient Information" style="max-height: 500px;">


**Note:**
> Currently blindbit-desktop does not support coin selection or Human Readable Names (HRN) addresses at this time
> 
> Fee rate will be increased to spend remaining UTXO to avoid dust
> 

---

#### Preview Transaction

Select "Confirm & Broadcast" to send the transaction

<img src="screenshots/sending_preview_transaction.png" alt="Preview Transaction" style="max-height: 500px;">


**Note:**
> Select "Close" to return to the previous view and make changes

---

#### Transaction Confirmation

Click "OK" to close broadcast response

<img src="screenshots/sending_transaction_confirmation.png" alt="Transaction Confirmation" style="max-height: 500px;">



---

#### Pending Transactions

Unconfirmed transactions will have a "Pending" status

<img src="screenshots/sending_pending_transactions.png" alt="Pending Transactions" style="max-height: 500px;">


**Note:**
> Select a "transaction" to view details

---

#### Spent UTXOs

While a transaction is being confirmed the whole UTXO is treated as spent

<img src="screenshots/sending_spent_utxos.png" alt="Spent UTXOs" style="max-height: 500px;">


**Note:**
> Toggle "unspent" to view unconfirmed_status

---



 ***
## Receiving Transactions

Overview of receiving funds to blindbit-desktop

#### UTXOs

UTXOs will appear here automatically after confirmation

<img src="screenshots/receiving_utxos.png" alt="UTXOs" style="max-height: 500px;">



---

#### Transactions

- History of wallet transactions
- Select a "transaction" to view details

<img src="screenshots/receiving_transactions.png" alt="Transactions" style="max-height: 500px;">


**Note:**
> received transactions will appear here automatically when confirmed
> 

---






## Troubleshooting

### Screenshots Don't Match
- Verify the wallet was compiled from the correct branch "alpha"

### Sync Issues
- Verify your internet connection
- Check firewall settings
- Allow sufficient time for blockchain synchronization


### Need More Help?

- Report an issue in the project repository: https://github.com/setavenger/blindbit-desktop
- Join Silent Payments [discord](https://discord.gg/UFF2u6hxBf) and ask for help

---

*This guide is maintained automatically. If you notice any discrepancies, please report them.*