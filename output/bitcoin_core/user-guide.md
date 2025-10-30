# Bitcoin Core Wallet User Guide

> **Last Updated:** 2025-10-30

Bitcoin Core Wallet with Silent Payments Support

---

## Table of Contents

- [Building from Source](#building-from-source)
- [Initial Wallet Setup](#initial-wallet-setup)
- [Wallet Overview](#wallet-overview)
- [Sending Silent Payments](#sending-silent-payments)
- [Receiving Silent Payments](#receiving-silent-payments)
- [Troubleshooting](#troubleshooting)

---

## Building from Source

**Source Code:** https://github.com/Eunovo/bitcoin/tree/2025-implement-bip352-receiving

### Prerequisites
- Xcode Command Line Tools
- Qt6 - `brew install qt`

### Build Steps (Simplified) - Detailed [MacOS Reference](https://github.com/bitcoin/bitcoin/blob/master/doc/build-osx.md)
```bash
export QTDIR=/usr/local/opt/qt
git clone https://github.com/Eunovo/bitcoin
cd bitcoin
git checkout -B 2025-implement-bip352-receiving origin/2025-implement-bip352-receiving
cmake -B build -DBUILD_GUI=ON
cmake --build build -j 10 --target deploy
# You will need a synchronized full node to continue
./build/dist/Bitcoin-Qt.app/Contents/MacOS/Bitcoin-Qt -datadir=/Users/<user>/data/bitcoin -conf=/Users/<user>/.bitcoin/bitcoin.conf -server
```


---

 ***
## Initial Wallet Setup

Create and configure your wallet for silent payments

#### Create New Wallet

- Enter "Wallet Name"
- Check "Make Silent Payments Wallet"
- Select "Create" button

<img src="screenshots/setup_create_new_wallet.png" alt="Create New Wallet" style="max-height: 500px;">



---



 ***
## Wallet Overview


#### Overview

Main screen showing balance and recent transactions

<img src="screenshots/usage_overview.png" alt="Overview" style="max-height: 500px;">



---

#### Send

Send bitcoin to other wallets

<img src="screenshots/usage_send.png" alt="Send" style="max-height: 500px;">



---

#### Receive

- Copy silent payments address to share with others
- Go to [Receiving Silent Payments](#receiving-silent-payments) for more details

<img src="screenshots/usage_receive.png" alt="Receive" style="max-height: 500px;">


**Note:**
> Only one address is required, each transaction will have a unique on chain taproot address

---

#### Transactions

View transaction history

<img src="screenshots/usage_transactions.png" alt="Transactions" style="max-height: 500px;">


**Note:**
> transactions will appear as soon as they are broadcast to the network

---



 ***
## Sending Silent Payments


#### Enter Recipient Information

- Enter "Pay To"
- Enter "Amount"
- Select "Send"

<img src="screenshots/sending_enter_recipient_information_annotated.png" alt="Enter Recipient Information" style="max-height: 500px;">


**Note:**
> Currently Bitcoin Core does not support Human Readable Names (HRN) addresses

---

#### Confirm Transaction

- Review recipient information
- Select "Send" to broadcast transaction

<img src="screenshots/sending_confirm_transaction.png" alt="Confirm Transaction" style="max-height: 500px;">



---



 ***
## Receiving Silent Payments


#### Receive

There are 2 methods for finding the silent payment address in Bitcoin Core

<img src="screenshots/receiving_receive.png" alt="Receive" style="max-height: 500px;">



---

#### Make Silent Payment Request

- (1) Choose "Silent Payment" in address type dropdown
- Select "Create new receiving address" to generate requested silent payment history address

<img src="screenshots/receiving_make_silent_payment_request_annotated.png" alt="Make Silent Payment Request" style="max-height: 500px;">


**Note:**
> Once the silent payment entry is added to the list you can double-click the entry to re-open the view

---

#### Copy Silent Payment Address

Select "Copy Address" to copy to clipboard

<img src="screenshots/receiving_copy_silent_payment_address.png" alt="Copy Silent Payment Address" style="max-height: 500px;">



---

#### Find Silent Payment in Receiving Addresses

- Select "Window" in application menu
- Select "Receiving addresses" from menu
- Search for "sp" in the search field
- Select the address with "sp1q" prefix from the Address list
- Select "Copy"

<img src="screenshots/receiving_find_silent_payment_in_receiving_addresses.png" alt="Find Silent Payment in Receiving Addresses" style="max-height: 500px;">



---






## Troubleshooting

### Common Issues

**Wallet won't start:**
- Check that you have the required dependencies installed
- Verify the application path is correct

**Screenshots don't match:**
- Ensure you're using the correct version
- Check that you compiled from the correct branch


### Need More Help?

- Report an issue in the project repository: https://github.com/Eunovo/bitcoin/tree/2025-implement-bip352-receiving
- Join Silent Payments [discord](https://discord.gg/UFF2u6hxBf) and ask for help

---

*This guide is maintained automatically. If you notice any discrepancies, please report them.*