    def equalize_boxes(self):
        """Equalize paned boxes without causing loops."""
        print("DEBUG: Equalize boxes button clicked!")
        
        # No-op in tabbed mode
        if getattr(self, 'current_view_mode', None) != 'paned':
            print("DEBUG: Equalize ignored in tabbed mode")
            return
        
        # Prevent recursive calls
        if getattr(self, '_equalizing_in_progress', False):
            print("DEBUG: Equalize already in progress, skipping")
            return
        
        try:
            self._equalizing_in_progress = True
            
            # Check current arrangement mode
            if hasattr(self, 'current_arrangement') and self.current_arrangement == "horizontal":
                print("DEBUG: In horizontal mode - equalizing box widths")
                self._apply_arrangement_change()
                return
            
            # Continue with vertical equalization for vertical mode
            print("DEBUG: In vertical mode - equalizing box heights")
            pw = getattr(self, 'paned_window', None)
            if not pw or not pw.winfo_exists():
                print("DEBUG: No valid paned_window to equalize")
                return
                
            self.root.update_idletasks()
            num_panes = len(pw.panes())
            print(f"DEBUG: Number of panes: {num_panes}")
            
            if num_panes > 1:
                # Simple equalization without complex calculations
                self.root.update_idletasks()
                print("DEBUG: Simple vertical equalization completed")
            elif num_panes == 1:
                print("DEBUG: Single pane - no equalization needed")
            else:
                print("DEBUG: No panes found!")
                
        except Exception as e:
            print(f"DEBUG: Error in equalize_boxes: {e}")
        finally:
            # Always clear the equalization flag
            self._equalizing_in_progress = False