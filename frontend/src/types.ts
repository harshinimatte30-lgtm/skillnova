export type Role='student'|'company'|'academician'|'admin';
export interface User{ id:number; email:string; role:Role; name:string }
export interface Skill{ id:number; name:string; category:string }
export interface RoleOption{ id:number; name:string; description:string }
export interface Profile{ id:number; name:string; email:string; education:string; year_degree:string; target_role_id:number|null; target_role:string|null; career_interests:string; research_experience:string; achievements:string; skills:{id:number;skill_id:number;skill:string;proficiency:number}[]; projects:{id:number;title:string;description:string;url:string}[]; certificates:{id:number;title:string;issuer:string;url:string}[]; courses:{id:number;title:string;provider:string;url:string}[] }
