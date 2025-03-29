class ScoutingForm {
    constructor(formId) {
        // Form elements
        this.form = document.getElementById(formId);
        this.minusBtns = this.form.querySelectorAll('.counter-btn.counter-minus');
        this.plusBtns = this.form.querySelectorAll('.counter-btn.counter-plus');
        this.counters = this.form.querySelectorAll('.counter');
        this.undoButtons = this.form.querySelectorAll('#undoButton');
        
        // Teleop cycle tracking
        this.teleopCycles = this.form.querySelector('input[name="teleop_cycles"]');
        this.teleopSuccessfulCycles = this.form.querySelector('input[name="teleop_successful_cycles"]');
        this.totalMissed = 0;
        this.totalSuccessful = 0;
        
        // Action history for undo functionality
        this.actionHistory = [];
        
        // Initialize the form
        this.init();
    }
    
    init() {
        // Check if already initialized to prevent duplicate event listeners
        if (this.form.dataset.initialized === 'true') {
            return;
        }
        
        this.setupButtonLabels();
        this.setupCounterButtons();
        this.setupUndoButtons();
        
        // Mark as initialized
        this.form.dataset.initialized = 'true';
    }
    
    setupButtonLabels() {
        // Set labels for minus buttons
        this.minusBtns.forEach(btn => {
            if (!btn.disabled) {
                btn.textContent = "M";
                btn.title = "Missed Attempt";
            }
        });
        
        // Set labels for plus buttons
        this.plusBtns.forEach(btn => {
            if (!btn.disabled) {
                btn.textContent = "S";
                btn.title = "Successful Attempt";
            }
        });
    }
    
    setupCounterButtons() {
        // Set up minus buttons (missed attempts)
        this.minusBtns.forEach(btn => {
            if (btn.disabled) return;
            
            // Add a check to prevent duplicate listeners
            if (btn.dataset.hasListener === 'true') return;
            
            btn.addEventListener('click', () => {
                const counter = btn.closest('.counter');
                const input = counter.querySelector('input');
                
                // Skip cycle total inputs
                if (input.name === 'teleop_cycles' || input.name === 'teleop_successful_cycles') {
                    return;
                }
                
                const oldValue = parseInt(input.value) || 0;
                input.value = oldValue + 1;
                
                // Update teleop cycle totals if applicable
                if (input.name.startsWith('teleop_')) {
                    this.totalMissed++;
                    this.updateTotals();
                }
                
                this.recordAction(input.name, oldValue, parseInt(input.value));
            });
            
            // Mark as having a listener
            btn.dataset.hasListener = 'true';
        });
        
        // Set up plus buttons (successful attempts)
        this.plusBtns.forEach(btn => {
            if (btn.disabled) return;
            
            // Add a check to prevent duplicate listeners
            if (btn.dataset.hasListener === 'true') return;
            
            btn.addEventListener('click', () => {
                const counter = btn.closest('.counter');
                const input = counter.querySelector('input');
                
                // Skip cycle total inputs
                if (input.name === 'teleop_cycles' || input.name === 'teleop_successful_cycles') {
                    return;
                }
                
                const oldValue = parseInt(input.value) || 0;
                input.value = oldValue + 1;
                
                // Update teleop cycle totals if applicable
                if (input.name.startsWith('teleop_')) {
                    this.totalSuccessful++;
                    this.updateTotals();
                }
                
                this.recordAction(input.name, oldValue, parseInt(input.value));
            });
            
            // Mark as having a listener
            btn.dataset.hasListener = 'true';
        });
    }
    
    setupUndoButtons() {
        this.undoButtons.forEach(btn => {
            btn.addEventListener('click', () => this.undoLastAction());
        });
    }
    
    updateTotals() {
        if (this.teleopCycles) {
            this.teleopCycles.value = this.totalMissed + this.totalSuccessful;
        }
        
        if (this.teleopSuccessfulCycles) {
            this.teleopSuccessfulCycles.value = this.totalSuccessful;
        }
    }
    
    recordAction(inputName, oldValue, newValue) {
        this.actionHistory.push({
            inputName: inputName,
            oldValue: oldValue,
            newValue: newValue,
            isMissed: inputName.includes('_missed') || inputName.includes('counter-minus')
        });
    }
    
    undoLastAction() {
        if (this.actionHistory.length === 0) {
            return;
        }
        
        const lastAction = this.actionHistory.pop();
        const input = this.form.querySelector(`input[name="${lastAction.inputName}"]`);
        
        if (input) {
            // Restore the previous value
            input.value = lastAction.oldValue;
            
            // Update teleop cycle totals if needed
            if (lastAction.inputName.startsWith('teleop_')) {
                const diff = parseInt(lastAction.newValue) - parseInt(lastAction.oldValue);
                
                if (lastAction.isMissed || lastAction.inputName.includes('_missed')) {
                    this.totalMissed -= diff;
                } else {
                    this.totalSuccessful -= diff;
                }
                
                this.updateTotals();
            }
        }
    }
}

// Ensure only one instance is created
let scoutingFormInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    const formElement = document.getElementById('scout-form');
    if (formElement && !scoutingFormInstance) {
        scoutingFormInstance = new ScoutingForm('scout-form');
    }
});