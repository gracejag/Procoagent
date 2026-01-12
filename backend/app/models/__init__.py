cat > app/models/__init__.py << 'EOF'
from .user import User
from .business import Business
from .transaction import Transaction

__all__ = ["User", "Business", "Transaction"]
EOF
