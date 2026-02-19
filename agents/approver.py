"""
Approver Agent - Orchestrates workflow and quality gates
"""
import os
from typing import Dict, Any
from supabase import Client

class ApproverAgent:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check quality gates and determine next status"""
        draft_id = input_data.get('draft_id')
        
        # Get all quality gates
        gates = self.supabase.table('quality_gates').select('*').eq('request_id', draft_id).execute()
        
        quality_results = {}
        all_passed = True
        
        for gate in gates.data:
            quality_results[gate['gate_name']] = {
                'passed': gate['passed'],
                'value': gate.get('value', {})
            }
            if not gate['passed']:
                all_passed = False
        
        # Determine next status
        if all_passed:
            new_status = 'staff_review'
        else:
            new_status = 'ai_review'  # Send back for revision
        
        # Update draft status
        self.supabase.table('drafts').update({
            'workflow_status': new_status,
            'updated_at': 'now()'
        }).eq('id', draft_id).execute()
        
        return {
            'status': new_status,
            'quality_gates': quality_results,
            'all_passed': all_passed
        }
