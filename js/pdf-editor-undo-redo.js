/**
 * PDF Editor Undo/Redo Module
 * History stack for undo/redo functionality
 */

export class UndoRedoController {
    constructor(config) {
        this.maxHistory = config.maxHistory || 50;
        this.history = [];
        this.currentIndex = -1;
        this.onStateChange = config.onStateChange || (() => {});
        this.isUndoing = false;
    }
    
    saveState(state) {
        if (this.isUndoing) return;
        
        // Remove any states after current index (when user does new action after undo)
        this.history = this.history.slice(0, this.currentIndex + 1);
        
        // Add new state
        this.history.push(JSON.parse(JSON.stringify(state))); // Deep clone
        
        // Limit history size
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.currentIndex++;
        }
    }
    
    undo() {
        if (!this.canUndo()) return null;
        
        this.isUndoing = true;
        this.currentIndex--;
        const state = this.history[this.currentIndex];
        this.onStateChange(state, 'undo');
        this.isUndoing = false;
        return state;
    }
    
    redo() {
        if (!this.canRedo()) return null;
        
        this.isUndoing = true;
        this.currentIndex++;
        const state = this.history[this.currentIndex];
        this.onStateChange(state, 'redo');
        this.isUndoing = false;
        return state;
    }
    
    canUndo() {
        return this.currentIndex > 0;
    }
    
    canRedo() {
        return this.currentIndex < this.history.length - 1;
    }
    
    clear() {
        this.history = [];
        this.currentIndex = -1;
    }
    
    getCurrentState() {
        if (this.currentIndex >= 0 && this.currentIndex < this.history.length) {
            return this.history[this.currentIndex];
        }
        return null;
    }
}

