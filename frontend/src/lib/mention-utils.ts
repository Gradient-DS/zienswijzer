import type { StakeholderMention, ChunkDetail } from '@/types';

/**
 * Transform backend mention data (with verified field) to frontend format (with checked/accepted/rejected)
 */
export function transformMention(mention: any): StakeholderMention {
    const verified = mention.verified;
    // If verified is null/undefined, the mention hasn't been checked yet
    const checked = verified !== null && verified !== undefined;

    if (!checked) {
        // Unchecked mention
        return {
            ...mention,
            checked: false,
            accepted: null,
            rejected: null,
        };
    }

    // Checked mention - verified is either true (accepted) or false (rejected)
    const verifiedBool = verified === true || verified === 1;
    return {
        ...mention,
        checked: true,
        accepted: verifiedBool ? true : null,
        rejected: verifiedBool ? null : true,
    };
}

/**
 * Transform chunk detail with mentions
 */
export function transformChunkDetail(chunk: any): ChunkDetail {
    return {
        ...chunk,
        stakeholder_mentions: chunk.stakeholder_mentions?.map(transformMention) || [],
    };
}

/**
 * Transform verified value back to backend format
 * Maps checked/accepted/rejected to verified boolean
 */
export function transformVerifiedToBackend(checked: boolean, accepted: boolean | null, rejected: boolean | null): boolean {
    // Backend doesn't accept null, so we need to convert unchecked to a boolean
    // If checked is false, we shouldn't be calling this, but default to false (rejected/unchecked)
    if (!checked) {
        // This shouldn't happen in normal flow, but handle it defensively
        return false;
    }

    // If explicitly accepted, return true
    if (accepted === true) {
        return true;
    }

    // If explicitly rejected, return false
    if (rejected === true) {
        return false;
    }

    // If checked but neither accepted nor rejected is explicitly true,
    // this is an invalid state - default to false (rejected)
    return false;
}

