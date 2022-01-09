def approve(self, token: AddressLike, max_approval: Optional[int] = None) -> None:
    """Give an exchange/router max approval of a token."""
    max_approval = self.max_approval_int if not max_approval else max_approval
    contract_addr = (
        self._exchange_address_from_token(token)
        if self.version == 1
        else self.router_address
    )
    function = _load_contract_erc20(self.w3, token).functions.approve(
        contract_addr, max_approval
    )
    logger.warning(f"Approving {_addr_to_str(token)}...")
    tx = self._build_and_send_tx(function)
    self.w3.eth.wait_for_transaction_receipt(tx, timeout=6000)

    # Add extra sleep to let tx propogate correctly
    time.sleep(1)


def _is_approved(self, token: AddressLike) -> bool:
    """Check to see if the exchange and token is approved."""
    _validate_address(token)
    if self.version == 1:
        contract_addr = self._exchange_address_from_token(token)
    elif self.version in [2, 3]:
        contract_addr = self.router_address
    amount = (
        _load_contract_erc20(self.w3, token)
            .functions.allowance(self.address, contract_addr)
            .call()
    )
    if amount >= self.max_approval_check_int:
        return True
    else:
        return False