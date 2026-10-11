import pandas as pd

def compute_signatures(df: pd.DataFrame):
    """
    Computes deterministic source and destination signatures from non-label flow attributes.
    This creates flow-derived interaction nodes since UNSW-NB15 lacks IP addresses.
    """
    # Create deterministic string signatures based on available attributes
    # Convert numeric attributes to strings
    
    src_signatures = (
        df['proto'].astype(str) + "_" +
        df['state'].astype(str) + "_" +
        df['sttl'].astype(str) + "_" +
        df['swin'].astype(str) + "_" +
        df['ct_src_ltm'].astype(str)
    )
    
    dst_signatures = (
        df['service'].astype(str) + "_" +
        df['state'].astype(str) + "_" +
        df['dttl'].astype(str) + "_" +
        df['dwin'].astype(str) + "_" +
        df['ct_srv_dst'].astype(str)
    )
    
    return src_signatures, dst_signatures

def build_node_mapping(src_signatures, dst_signatures):
    """
    Creates a deterministic mapping from unique signatures to node IDs.
    """
    all_nodes = sorted(list(set(src_signatures) | set(dst_signatures)))
    
    node_map = {node: idx for idx, node in enumerate(all_nodes)}
    
    return node_map, all_nodes
