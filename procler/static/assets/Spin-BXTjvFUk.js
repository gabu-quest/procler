import{bx as J,by as X,bz as I,bA as w,V as h,ac as v,X as W,bB as Q,U as j,d as k,x as c,s as Y,bC as q,ak as Z,af as ee,bD as oe,Y as A,Z as B,aD as N,p as T,be as te,a0 as m,a1 as O,r as _,P as ne,R as re,W as se,Q as ie,S as le,bE as ae,m as ce,bF as de,bG as ue,bH as pe,aN as fe,bI as ge,bJ as me,aL as L,bK as he,aS as ve,ae as be,aX as Ce,b4 as ye,aJ as xe,bL as ze}from"./index-BzW1XhyH.js";import{g as Se}from"./Tag-Bh_qV63A.js";function Ie(e){const{lineHeight:o,borderRadius:r,fontWeightStrong:a,baseColor:n,dividerColor:i,actionColor:g,textColor1:l,textColor2:t,closeColorHover:d,closeColorPressed:p,closeIconColor:f,closeIconColorHover:b,closeIconColorPressed:u,infoColor:s,successColor:S,warningColor:C,errorColor:$,fontSize:y}=e;return Object.assign(Object.assign({},X),{fontSize:y,lineHeight:o,titleFontWeight:a,borderRadius:r,border:`1px solid ${i}`,color:g,titleTextColor:l,iconColor:t,contentTextColor:t,closeBorderRadius:r,closeColorHover:d,closeColorPressed:p,closeIconColor:f,closeIconColorHover:b,closeIconColorPressed:u,borderInfo:`1px solid ${I(n,w(s,{alpha:.25}))}`,colorInfo:I(n,w(s,{alpha:.08})),titleTextColorInfo:l,iconColorInfo:s,contentTextColorInfo:t,closeColorHoverInfo:d,closeColorPressedInfo:p,closeIconColorInfo:f,closeIconColorHoverInfo:b,closeIconColorPressedInfo:u,borderSuccess:`1px solid ${I(n,w(S,{alpha:.25}))}`,colorSuccess:I(n,w(S,{alpha:.08})),titleTextColorSuccess:l,iconColorSuccess:S,contentTextColorSuccess:t,closeColorHoverSuccess:d,closeColorPressedSuccess:p,closeIconColorSuccess:f,closeIconColorHoverSuccess:b,closeIconColorPressedSuccess:u,borderWarning:`1px solid ${I(n,w(C,{alpha:.33}))}`,colorWarning:I(n,w(C,{alpha:.08})),titleTextColorWarning:l,iconColorWarning:C,contentTextColorWarning:t,closeColorHoverWarning:d,closeColorPressedWarning:p,closeIconColorWarning:f,closeIconColorHoverWarning:b,closeIconColorPressedWarning:u,borderError:`1px solid ${I(n,w($,{alpha:.25}))}`,colorError:I(n,w($,{alpha:.08})),titleTextColorError:l,iconColorError:$,contentTextColorError:t,closeColorHoverError:d,closeColorPressedError:p,closeIconColorError:f,closeIconColorHoverError:b,closeIconColorPressedError:u})}const we={common:J,self:Ie},$e=h("alert",`
 line-height: var(--n-line-height);
 border-radius: var(--n-border-radius);
 position: relative;
 transition: background-color .3s var(--n-bezier);
 background-color: var(--n-color);
 text-align: start;
 word-break: break-word;
`,[v("border",`
 border-radius: inherit;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 transition: border-color .3s var(--n-bezier);
 border: var(--n-border);
 pointer-events: none;
 `),W("closable",[h("alert-body",[v("title",`
 padding-right: 24px;
 `)])]),v("icon",{color:"var(--n-icon-color)"}),h("alert-body",{padding:"var(--n-padding)"},[v("title",{color:"var(--n-title-text-color)"}),v("content",{color:"var(--n-content-text-color)"})]),Q({originalTransition:"transform .3s var(--n-bezier)",enterToProps:{transform:"scale(1)"},leaveToProps:{transform:"scale(0.9)"}}),v("icon",`
 position: absolute;
 left: 0;
 top: 0;
 align-items: center;
 justify-content: center;
 display: flex;
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 margin: var(--n-icon-margin);
 `),v("close",`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 position: absolute;
 right: 0;
 top: 0;
 margin: var(--n-close-margin);
 `),W("show-icon",[h("alert-body",{paddingLeft:"calc(var(--n-icon-margin-left) + var(--n-icon-size) + var(--n-icon-margin-right))"})]),W("right-adjust",[h("alert-body",{paddingRight:"calc(var(--n-close-size) + var(--n-padding) + 2px)"})]),h("alert-body",`
 border-radius: var(--n-border-radius);
 transition: border-color .3s var(--n-bezier);
 `,[v("title",`
 transition: color .3s var(--n-bezier);
 font-size: 16px;
 line-height: 19px;
 font-weight: var(--n-title-font-weight);
 `,[j("& +",[v("content",{marginTop:"9px"})])]),v("content",{transition:"color .3s var(--n-bezier)",fontSize:"var(--n-font-size)"})]),v("icon",{transition:"color .3s var(--n-bezier)"})]),Re=Object.assign(Object.assign({},B.props),{title:String,showIcon:{type:Boolean,default:!0},type:{type:String,default:"default"},bordered:{type:Boolean,default:!0},closable:Boolean,onClose:Function,onAfterLeave:Function,onAfterHide:Function}),Le=k({name:"Alert",inheritAttrs:!1,props:Re,slots:Object,setup(e){const{mergedClsPrefixRef:o,mergedBorderedRef:r,inlineThemeDisabled:a,mergedRtlRef:n}=A(e),i=B("Alert","-alert",$e,we,e,o),g=N("Alert",n,o),l=T(()=>{const{common:{cubicBezierEaseInOut:u},self:s}=i.value,{fontSize:S,borderRadius:C,titleFontWeight:$,lineHeight:y,iconSize:R,iconMargin:P,iconMarginRtl:E,closeIconSize:z,closeBorderRadius:M,closeSize:V,closeMargin:F,closeMarginRtl:G,padding:D}=s,{type:x}=e,{left:K,right:U}=te(P);return{"--n-bezier":u,"--n-color":s[m("color",x)],"--n-close-icon-size":z,"--n-close-border-radius":M,"--n-close-color-hover":s[m("closeColorHover",x)],"--n-close-color-pressed":s[m("closeColorPressed",x)],"--n-close-icon-color":s[m("closeIconColor",x)],"--n-close-icon-color-hover":s[m("closeIconColorHover",x)],"--n-close-icon-color-pressed":s[m("closeIconColorPressed",x)],"--n-icon-color":s[m("iconColor",x)],"--n-border":s[m("border",x)],"--n-title-text-color":s[m("titleTextColor",x)],"--n-content-text-color":s[m("contentTextColor",x)],"--n-line-height":y,"--n-border-radius":C,"--n-font-size":S,"--n-title-font-weight":$,"--n-icon-size":R,"--n-icon-margin":P,"--n-icon-margin-rtl":E,"--n-close-size":V,"--n-close-margin":F,"--n-close-margin-rtl":G,"--n-padding":D,"--n-icon-margin-left":K,"--n-icon-margin-right":U}}),t=a?O("alert",T(()=>e.type[0]),l,e):void 0,d=_(!0),p=()=>{const{onAfterLeave:u,onAfterHide:s}=e;u&&u(),s&&s()};return{rtlEnabled:g,mergedClsPrefix:o,mergedBordered:r,visible:d,handleCloseClick:()=>{var u;Promise.resolve((u=e.onClose)===null||u===void 0?void 0:u.call(e)).then(s=>{s!==!1&&(d.value=!1)})},handleAfterLeave:()=>{p()},mergedTheme:i,cssVars:a?void 0:l,themeClass:t==null?void 0:t.themeClass,onRender:t==null?void 0:t.onRender}},render(){var e;return(e=this.onRender)===null||e===void 0||e.call(this),c(oe,{onAfterLeave:this.handleAfterLeave},{default:()=>{const{mergedClsPrefix:o,$slots:r}=this,a={class:[`${o}-alert`,this.themeClass,this.closable&&`${o}-alert--closable`,this.showIcon&&`${o}-alert--show-icon`,!this.title&&this.closable&&`${o}-alert--right-adjust`,this.rtlEnabled&&`${o}-alert--rtl`],style:this.cssVars,role:"alert"};return this.visible?c("div",Object.assign({},Y(this.$attrs,a)),this.closable&&c(q,{clsPrefix:o,class:`${o}-alert__close`,onClick:this.handleCloseClick}),this.bordered&&c("div",{class:`${o}-alert__border`}),this.showIcon&&c("div",{class:`${o}-alert__icon`,"aria-hidden":"true"},Z(r.icon,()=>[c(ne,{clsPrefix:o},{default:()=>{switch(this.type){case"success":return c(le,null);case"info":return c(ie,null);case"warning":return c(se,null);case"error":return c(re,null);default:return null}}})])),c("div",{class:[`${o}-alert-body`,this.mergedBordered&&`${o}-alert-body--bordered`]},ee(r.header,n=>{const i=n||this.title;return i?c("div",{class:`${o}-alert-body__title`},i):null}),r.default&&c("div",{class:`${o}-alert-body__content`},r))):null}})}});function Ne(){const e=ce(de,null);return e===null&&ae("use-message","No outer <n-message-provider /> founded. See prerequisite in https://www.naiveui.com/en-US/os-theme/components/message for more details. If you want to use `useMessage` outside setup, please check https://www.naiveui.com/zh-CN/os-theme/components/message#Q-&-A."),e}function Pe(){return ue}const Te={self:Pe};let H;function Be(){if(!pe)return!0;if(H===void 0){const e=document.createElement("div");e.style.display="flex",e.style.flexDirection="column",e.style.rowGap="1px",e.appendChild(document.createElement("div")),e.appendChild(document.createElement("div")),document.body.appendChild(e);const o=e.scrollHeight===1;return document.body.removeChild(e),H=o}return H}const Ee=Object.assign(Object.assign({},B.props),{align:String,justify:{type:String,default:"start"},inline:Boolean,vertical:Boolean,reverse:Boolean,size:{type:[String,Number,Array],default:"medium"},wrapItem:{type:Boolean,default:!0},itemClass:String,itemStyle:[String,Object],wrap:{type:Boolean,default:!0},internalUseGap:{type:Boolean,default:void 0}}),Oe=k({name:"Space",props:Ee,setup(e){const{mergedClsPrefixRef:o,mergedRtlRef:r}=A(e),a=B("Space","-space",void 0,Te,e,o),n=N("Space",r,o);return{useGap:Be(),rtlEnabled:n,mergedClsPrefix:o,margin:T(()=>{const{size:i}=e;if(Array.isArray(i))return{horizontal:i[0],vertical:i[1]};if(typeof i=="number")return{horizontal:i,vertical:i};const{self:{[m("gap",i)]:g}}=a.value,{row:l,col:t}=me(g);return{horizontal:L(t),vertical:L(l)}})}},render(){const{vertical:e,reverse:o,align:r,inline:a,justify:n,itemClass:i,itemStyle:g,margin:l,wrap:t,mergedClsPrefix:d,rtlEnabled:p,useGap:f,wrapItem:b,internalUseGap:u}=this,s=fe(Se(this),!1);if(!s.length)return null;const S=`${l.horizontal}px`,C=`${l.horizontal/2}px`,$=`${l.vertical}px`,y=`${l.vertical/2}px`,R=s.length-1,P=n.startsWith("space-");return c("div",{role:"none",class:[`${d}-space`,p&&`${d}-space--rtl`],style:{display:a?"inline-flex":"flex",flexDirection:e&&!o?"column":e&&o?"column-reverse":!e&&o?"row-reverse":"row",justifyContent:["start","end"].includes(n)?`flex-${n}`:n,flexWrap:!t||e?"nowrap":"wrap",marginTop:f||e?"":`-${y}`,marginBottom:f||e?"":`-${y}`,alignItems:r,gap:f?`${l.vertical}px ${l.horizontal}px`:""}},!b&&(f||u)?s:s.map((E,z)=>E.type===ge?E:c("div",{role:"none",class:i,style:[g,{maxWidth:"100%"},f?"":e?{marginBottom:z!==R?$:""}:p?{marginLeft:P?n==="space-between"&&z===R?"":C:z!==R?S:"",marginRight:P?n==="space-between"&&z===0?"":C:"",paddingTop:y,paddingBottom:y}:{marginRight:P?n==="space-between"&&z===R?"":C:z!==R?S:"",marginLeft:P?n==="space-between"&&z===0?"":C:"",paddingTop:y,paddingBottom:y}]},E)))}}),We=j([j("@keyframes spin-rotate",`
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
 `,[he()])]),h("spin-body",`
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
 `,[W("rotate",`
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
 `,[W("spinning",`
 user-select: none;
 -webkit-user-select: none;
 pointer-events: none;
 opacity: var(--n-opacity-spinning);
 `)])]),He={small:20,medium:18,large:16},je=Object.assign(Object.assign({},B.props),{contentClass:String,contentStyle:[Object,String],description:String,stroke:String,size:{type:[String,Number],default:"medium"},show:{type:Boolean,default:!0},strokeWidth:Number,rotate:{type:Boolean,default:!0},spinning:{type:Boolean,validator:()=>!0,default:void 0},delay:Number}),_e=k({name:"Spin",props:je,slots:Object,setup(e){const{mergedClsPrefixRef:o,inlineThemeDisabled:r}=A(e),a=B("Spin","-spin",We,ze,e,o),n=T(()=>{const{size:t}=e,{common:{cubicBezierEaseInOut:d},self:p}=a.value,{opacitySpinning:f,color:b,textColor:u}=p,s=typeof t=="number"?Ce(t):p[m("size",t)];return{"--n-bezier":d,"--n-opacity-spinning":f,"--n-size":s,"--n-color":b,"--n-text-color":u}}),i=r?O("spin",T(()=>{const{size:t}=e;return typeof t=="number"?String(t):t[0]}),n,e):void 0,g=ye(e,["spinning","show"]),l=_(!1);return xe(t=>{let d;if(g.value){const{delay:p}=e;if(p){d=window.setTimeout(()=>{l.value=!0},p),t(()=>{clearTimeout(d)});return}}l.value=g.value}),{mergedClsPrefix:o,active:l,mergedStrokeWidth:T(()=>{const{strokeWidth:t}=e;if(t!==void 0)return t;const{size:d}=e;return He[typeof d=="number"?"medium":d]}),cssVars:r?void 0:n,themeClass:i==null?void 0:i.themeClass,onRender:i==null?void 0:i.onRender}},render(){var e,o;const{$slots:r,mergedClsPrefix:a,description:n}=this,i=r.icon&&this.rotate,g=(n||r.description)&&c("div",{class:`${a}-spin-description`},n||((e=r.description)===null||e===void 0?void 0:e.call(r))),l=r.icon?c("div",{class:[`${a}-spin-body`,this.themeClass]},c("div",{class:[`${a}-spin`,i&&`${a}-spin--rotate`],style:r.default?"":this.cssVars},r.icon()),g):c("div",{class:[`${a}-spin-body`,this.themeClass]},c(ve,{clsPrefix:a,style:r.default?"":this.cssVars,stroke:this.stroke,"stroke-width":this.mergedStrokeWidth,class:`${a}-spin`}),g);return(o=this.onRender)===null||o===void 0||o.call(this),r.default?c("div",{class:[`${a}-spin-container`,this.themeClass],style:this.cssVars},c("div",{class:[`${a}-spin-content`,this.active&&`${a}-spin-content--spinning`,this.contentClass],style:this.contentStyle},r),c(be,{name:"fade-in-transition"},{default:()=>this.active?l:null})):l}});export{_e as N,Le as a,Oe as b,Ne as u};
