class TopologyGrammarEngine:
    """
    Module 3 and Module 8: Topology Genesis Engine & Topology Grammar Evolution.
    Learns valid graph transformations and supports versioned grammar evolution.
    """
    def __init__(self):
        self.grammar = set()
        self.versions = []
        
    def learn_from_training(self, train_graphs):
        """Learn valid edge transformations from training sequence."""
        for i in range(len(train_graphs) - 1):
            g1, g2 = train_graphs[i], train_graphs[i+1]
            edges1 = set(tuple(e) for e in g1['edge_index'].t().tolist())
            edges2 = set(tuple(e) for e in g2['edge_index'].t().tolist())
            
            added = edges2 - edges1
            removed = edges1 - edges2
            
            # Simple grammar rules based on degree ranges or specific nodes
            # For this proxy implementation, we store the frequency of node degree changes
            # A full implementation would use a learnable GNN rule set.
            for e in added:
                self.grammar.add(f"ADD_EDGE")
            for e in removed:
                self.grammar.add(f"REMOVE_EDGE")
                
        self._commit_version("Initial training grammar")
        
    def _commit_version(self, reason):
        self.versions.append({
            'version': len(self.versions) + 1,
            'grammar_state': set(self.grammar),
            'reason': reason
        })
        
    def evolve_grammar(self, candidate_transformations, validation_score, threshold=0.8):
        """
        Module 8: Validates and updates the legitimate grammar based on new observations.
        """
        accepted = 0
        rejected = 0
        
        # Validation gate check
        if validation_score > threshold:
            for t in candidate_transformations:
                if t not in self.grammar:
                    self.grammar.add(t)
                    accepted += 1
            if accepted > 0:
                self._commit_version("Grammar evolved based on high-confidence valid structural drift")
        else:
            rejected = len(candidate_transformations)
            
        return accepted, rejected
        
    def rollback(self):
        """Rollback to the previous grammar version."""
        if len(self.versions) > 1:
            self.versions.pop() # Remove current version
            self.grammar = set(self.versions[-1]['grammar_state']) # Restore to the state of the now-latest version
            return True
        return False
