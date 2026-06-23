"""
ot-ctl output parsers.

Each parser takes raw text output from a single ot-ctl command and returns
structured model objects. Parsers are pure functions with no side effects.

Step 2 status: parsers are STUBS. They will be implemented once real
ot-ctl output fixtures are provided from both OTBRs.

The build_snapshot_from_results() function is the main entry point used
by LocalDockerOtbrSource and SshDockerOtbrSource.
"""
from .state import parse_state
from .child_table import parse_child_table
from .neighbor_table import parse_neighbor_table
from .router_table import parse_router_table
from .dataset import parse_dataset_active
from .netdata import parse_netdata
from .ipaddr import parse_ipaddr
from .counters import parse_counters_mac, parse_counters_mle
from .srp import parse_srp_server_host, parse_srp_server_service
from .snapshot_builder import build_snapshot_from_results

__all__ = [
    "parse_state",
    "parse_child_table",
    "parse_neighbor_table",
    "parse_router_table",
    "parse_dataset_active",
    "parse_netdata",
    "parse_ipaddr",
    "parse_counters_mac",
    "parse_counters_mle",
    "parse_srp_server_host",
    "parse_srp_server_service",
    "build_snapshot_from_results",
]
