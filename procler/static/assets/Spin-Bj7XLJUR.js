import{a9 as P,q as G,bE as O,bF as V,bC as W,d as E,bd as M,p as c,bG as L,Q as I,S as w,U as A,s as S,am as T,bH as H,ax as R,L as j,I as h,bI as D,K as k,aE as K,aj as U,ay as F,V as _,b7 as q,r as J,aP as Q,bJ as X}from"./index-CLWh9w0Y.js";import{g as Y}from"./Tag-B5XemjLL.js";function le(){const e=G(O,null);return e===null&&P("use-message","No outer <n-message-provider /> founded. See prerequisite in https://www.naiveui.com/en-US/os-theme/components/message for more details. If you want to use `useMessage` outside setup, please check https://www.naiveui.com/zh-CN/os-theme/components/message#Q-&-A."),e}function Z(){return V}const ee={self:Z};let $;function te(){if(!W)return!0;if($===void 0){const e=document.createElement("div");e.style.display="flex",e.style.flexDirection="column",e.style.rowGap="1px",e.appendChild(document.createElement("div")),e.appendChild(document.createElement("div")),document.body.appendChild(e);const s=e.scrollHeight===1;return document.body.removeChild(e),$=s}return $}const ne=Object.assign(Object.assign({},w.props),{align:String,justify:{type:String,default:"start"},inline:Boolean,vertical:Boolean,reverse:Boolean,size:{type:[String,Number,Array],default:"medium"},wrapItem:{type:Boolean,default:!0},itemClass:String,itemStyle:[String,Object],wrap:{type:Boolean,default:!0},internalUseGap:{type:Boolean,default:void 0}}),ce=E({name:"Space",props:ne,setup(e){const{mergedClsPrefixRef:s,mergedRtlRef:n}=I(e),i=w("Space","-space",void 0,ee,e,s),a=A("Space",n,s);return{useGap:te(),rtlEnabled:a,mergedClsPrefix:s,margin:S(()=>{const{size:t}=e;if(Array.isArray(t))return{horizontal:t[0],vertical:t[1]};if(typeof t=="number")return{horizontal:t,vertical:t};const{self:{[T("gap",t)]:p}}=i.value,{row:r,col:o}=H(p);return{horizontal:R(o),vertical:R(r)}})}},render(){const{vertical:e,reverse:s,align:n,inline:i,justify:a,itemClass:t,itemStyle:p,margin:r,wrap:o,mergedClsPrefix:l,rtlEnabled:d,useGap:u,wrapItem:x,internalUseGap:z}=this,f=M(Y(this),!1);if(!f.length)return null;const B=`${r.horizontal}px`,y=`${r.horizontal/2}px`,N=`${r.vertical}px`,g=`${r.vertical/2}px`,v=f.length-1,b=a.startsWith("space-");return c("div",{role:"none",class:[`${l}-space`,d&&`${l}-space--rtl`],style:{display:i?"inline-flex":"flex",flexDirection:e&&!s?"column":e&&s?"column-reverse":!e&&s?"row-reverse":"row",justifyContent:["start","end"].includes(a)?`flex-${a}`:a,flexWrap:!o||e?"nowrap":"wrap",marginTop:u||e?"":`-${g}`,marginBottom:u||e?"":`-${g}`,alignItems:n,gap:u?`${r.vertical}px ${r.horizontal}px`:""}},!x&&(u||z)?f:f.map((C,m)=>C.type===L?C:c("div",{role:"none",class:t,style:[p,{maxWidth:"100%"},u?"":e?{marginBottom:m!==v?N:""}:d?{marginLeft:b?a==="space-between"&&m===v?"":y:m!==v?B:"",marginRight:b?a==="space-between"&&m===0?"":y:"",paddingTop:g,paddingBottom:g}:{marginRight:b?a==="space-between"&&m===v?"":y:m!==v?B:"",marginLeft:b?a==="space-between"&&m===0?"":y:"",paddingTop:g,paddingBottom:g}]},C)))}}),se=j([j("@keyframes spin-rotate",`
 from {
 transform: rotate(0);
 }
 to {
 transform: rotate(360deg);
 }
 `),h("spin-container",`
 position: relative;
 `,[h("spin-body",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[D()])]),h("spin-body",`
 display: inline-flex;
 align-items: center;
 justify-content: center;
 flex-direction: column;
 `),h("spin",`
 display: inline-flex;
 height: var(--n-size);
 width: var(--n-size);
 font-size: var(--n-size);
 color: var(--n-color);
 `,[k("rotate",`
 animation: spin-rotate 2s linear infinite;
 `)]),h("spin-description",`
 display: inline-block;
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 margin-top: 8px;
 `),h("spin-content",`
 opacity: 1;
 transition: opacity .3s var(--n-bezier);
 pointer-events: all;
 `,[k("spinning",`
 user-select: none;
 -webkit-user-select: none;
 pointer-events: none;
 opacity: var(--n-opacity-spinning);
 `)])]),ie={small:20,medium:18,large:16},ae=Object.assign(Object.assign({},w.props),{contentClass:String,contentStyle:[Object,String],description:String,stroke:String,size:{type:[String,Number],default:"medium"},show:{type:Boolean,default:!0},strokeWidth:Number,rotate:{type:Boolean,default:!0},spinning:{type:Boolean,validator:()=>!0,default:void 0},delay:Number}),pe=E({name:"Spin",props:ae,slots:Object,setup(e){const{mergedClsPrefixRef:s,inlineThemeDisabled:n}=I(e),i=w("Spin","-spin",se,X,e,s),a=S(()=>{const{size:o}=e,{common:{cubicBezierEaseInOut:l},self:d}=i.value,{opacitySpinning:u,color:x,textColor:z}=d,f=typeof o=="number"?F(o):d[T("size",o)];return{"--n-bezier":l,"--n-opacity-spinning":u,"--n-size":f,"--n-color":x,"--n-text-color":z}}),t=n?_("spin",S(()=>{const{size:o}=e;return typeof o=="number"?String(o):o[0]}),a,e):void 0,p=q(e,["spinning","show"]),r=J(!1);return Q(o=>{let l;if(p.value){const{delay:d}=e;if(d){l=window.setTimeout(()=>{r.value=!0},d),o(()=>{clearTimeout(l)});return}}r.value=p.value}),{mergedClsPrefix:s,active:r,mergedStrokeWidth:S(()=>{const{strokeWidth:o}=e;if(o!==void 0)return o;const{size:l}=e;return ie[typeof l=="number"?"medium":l]}),cssVars:n?void 0:a,themeClass:t==null?void 0:t.themeClass,onRender:t==null?void 0:t.onRender}},render(){var e,s;const{$slots:n,mergedClsPrefix:i,description:a}=this,t=n.icon&&this.rotate,p=(a||n.description)&&c("div",{class:`${i}-spin-description`},a||((e=n.description)===null||e===void 0?void 0:e.call(n))),r=n.icon?c("div",{class:[`${i}-spin-body`,this.themeClass]},c("div",{class:[`${i}-spin`,t&&`${i}-spin--rotate`],style:n.default?"":this.cssVars},n.icon()),p):c("div",{class:[`${i}-spin-body`,this.themeClass]},c(K,{clsPrefix:i,style:n.default?"":this.cssVars,stroke:this.stroke,"stroke-width":this.mergedStrokeWidth,class:`${i}-spin`}),p);return(s=this.onRender)===null||s===void 0||s.call(this),n.default?c("div",{class:[`${i}-spin-container`,this.themeClass],style:this.cssVars},c("div",{class:[`${i}-spin-content`,this.active&&`${i}-spin-content--spinning`,this.contentClass],style:this.contentStyle},n),c(U,{name:"fade-in-transition"},{default:()=>this.active?r:null})):r}});export{pe as N,ce as a,le as u};
