import React from 'react';
import { render, screen } from '@testing-library/react';
import { PipelineSteps } from '../PipelineSteps';
import '@testing-library/jest-dom';

describe('PipelineSteps Component', () => {
    const STAGES = [
        "Intake", "Drafting JD", "JD Review", "Sourcing", 
        "Screening", "Shortlist", "Interviews", "Decision", 
        "Offer", "Completed"
    ];

    it('renders all stage labels', () => {
        render(<PipelineSteps currentStage="intake" />);
        
        STAGES.forEach(label => {
            expect(screen.getByText(label)).toBeInTheDocument();
        });
    });

    it('highlights the active stage (Drafting)', () => {
        render(<PipelineSteps currentStage="jd_drafting" />);
        
        // Drafting is the 2nd stage (index 1)
        const draftingLabel = screen.getByText('Drafting JD');
        expect(draftingLabel).toHaveStyle({ fontWeight: '700' });
    });

    it('handles unknown stages gracefully by falling back to first stage', () => {
        render(<PipelineSteps currentStage="unknown_stage" />);
        const firstLabel = screen.getByText('Intake');
        expect(firstLabel).toHaveStyle({ fontWeight: '700' });
    });
});
