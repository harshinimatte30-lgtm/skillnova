import {ReactNode} from 'react';
export function Card({children,className='' }:{children:ReactNode;className?:string}){return <div className={`card ${className}`}>{children}</div>}
export function Stat({label,value,sub}:{label:string;value:string|number;sub?:string}){return <Card><div className="stat-label">{label}</div><div className="stat-value">{value}</div>{sub&&<div className="muted">{sub}</div>}</Card>}
export function Progress({value}:{value:number}){return <div className="progress"><span style={{width:`${Math.max(0,Math.min(100,value))}%`}}/></div>}
export function Empty({title,body}:{title:string;body:string}){return <div className="empty"><strong>{title}</strong><span>{body}</span></div>}
