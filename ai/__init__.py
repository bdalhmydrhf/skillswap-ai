# هذا الملف يجعل مجلد 'ai' وحدة Python صالحة للاستيراد

from .blockchain import (
    # Core functions
    sign_contract_with_biometric,
    verify_contract_signature,
    get_contract_signature_status,
    blockchain_health_check,
    liveness_probe,
    readiness_probe,
    
    # Exceptions
    EnterpriseBlockchainError,
    SigningError,
    RateLimitExceededError,
    BiometricUnavailableError,
    
    # Ledger (for advanced users)
    ContractLedger,
    LedgerEntry,
    LedgerEntryType,
    
    # Services
    BiometricService,
    get_biometric_service,
)

# قائمة بالدوال التي يمكن استيرادها بـ from ai import *
__all__ = [
    # Core functions
    'sign_contract_with_biometric',
    'verify_contract_signature',
    'get_contract_signature_status',
    'blockchain_health_check',
    'liveness_probe',
    'readiness_probe',
    
    # Exceptions
    'EnterpriseBlockchainError',
    'SigningError',
    'RateLimitExceededError',
    'BiometricUnavailableError',
    
    # Ledger
    'ContractLedger',
    'LedgerEntry',
    'LedgerEntryType',
    
    # Services
    'BiometricService',
    'get_biometric_service',
]
