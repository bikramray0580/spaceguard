# SpaceGuard Frontend Phase 4

## Dashboard real-threat integration

The dashboard now consumes the same backend-driven threat feed used by the Risk workspace. The compact Priority Monitor surfaces the highest-ranked screened conjunction and exposes miss distance, relative velocity, TCA, and risk level. Selecting the threat opens the existing Risk context panel without replacing the protected Simulation implementation.

The card also distinguishes loading, partial, error, and connected states. It does not create or fabricate threat values.
