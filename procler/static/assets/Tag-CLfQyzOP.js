import{bp as ao,bK as no,bs as e,R as so,S as p,$ as x,aj as I,T as z,d as to,a3 as N,z as y,bu as io,r as ho,U as go,V as D,Y as bo,a4 as Co,av as vo,p as U,a7 as h,b6 as uo,a8 as po,bL as V,ah as fo,Q as ko}from"./index-DkDVBGts.js";function Bo(l,i="default",r=[]){const c=l.$slots[i];return c===void 0?r:c()}function mo(l){const{textColor2:i,primaryColorHover:r,primaryColorPressed:C,primaryColor:c,infoColor:d,successColor:s,warningColor:n,errorColor:t,baseColor:f,borderColor:k,opacityDisabled:g,tagColor:v,closeIconColor:o,closeIconColorHover:a,closeIconColorPressed:u,borderRadiusSmall:b,fontSizeMini:m,fontSizeTiny:S,fontSizeSmall:B,fontSizeMedium:$,heightMini:H,heightTiny:R,heightSmall:M,heightMedium:T,closeColorHover:E,closeColorPressed:_,buttonColor2Hover:j,buttonColor2Pressed:O,fontWeightStrong:W}=l;return Object.assign(Object.assign({},no),{closeBorderRadius:b,heightTiny:H,heightSmall:R,heightMedium:M,heightLarge:T,borderRadius:b,opacityDisabled:g,fontSizeTiny:m,fontSizeSmall:S,fontSizeMedium:B,fontSizeLarge:$,fontWeightStrong:W,textColorCheckable:i,textColorHoverCheckable:i,textColorPressedCheckable:i,textColorChecked:f,colorCheckable:"#0000",colorHoverCheckable:j,colorPressedCheckable:O,colorChecked:c,colorCheckedHover:r,colorCheckedPressed:C,border:`1px solid ${k}`,textColor:i,color:v,colorBordered:"rgb(250, 250, 252)",closeIconColor:o,closeIconColorHover:a,closeIconColorPressed:u,closeColorHover:E,closeColorPressed:_,borderPrimary:`1px solid ${e(c,{alpha:.3})}`,textColorPrimary:c,colorPrimary:e(c,{alpha:.12}),colorBorderedPrimary:e(c,{alpha:.1}),closeIconColorPrimary:c,closeIconColorHoverPrimary:c,closeIconColorPressedPrimary:c,closeColorHoverPrimary:e(c,{alpha:.12}),closeColorPressedPrimary:e(c,{alpha:.18}),borderInfo:`1px solid ${e(d,{alpha:.3})}`,textColorInfo:d,colorInfo:e(d,{alpha:.12}),colorBorderedInfo:e(d,{alpha:.1}),closeIconColorInfo:d,closeIconColorHoverInfo:d,closeIconColorPressedInfo:d,closeColorHoverInfo:e(d,{alpha:.12}),closeColorPressedInfo:e(d,{alpha:.18}),borderSuccess:`1px solid ${e(s,{alpha:.3})}`,textColorSuccess:s,colorSuccess:e(s,{alpha:.12}),colorBorderedSuccess:e(s,{alpha:.1}),closeIconColorSuccess:s,closeIconColorHoverSuccess:s,closeIconColorPressedSuccess:s,closeColorHoverSuccess:e(s,{alpha:.12}),closeColorPressedSuccess:e(s,{alpha:.18}),borderWarning:`1px solid ${e(n,{alpha:.35})}`,textColorWarning:n,colorWarning:e(n,{alpha:.15}),colorBorderedWarning:e(n,{alpha:.12}),closeIconColorWarning:n,closeIconColorHoverWarning:n,closeIconColorPressedWarning:n,closeColorHoverWarning:e(n,{alpha:.12}),closeColorPressedWarning:e(n,{alpha:.18}),borderError:`1px solid ${e(t,{alpha:.23})}`,textColorError:t,colorError:e(t,{alpha:.1}),colorBorderedError:e(t,{alpha:.08}),closeIconColorError:t,closeIconColorHoverError:t,closeIconColorPressedError:t,closeColorHoverError:e(t,{alpha:.12}),closeColorPressedError:e(t,{alpha:.18})})}const xo={common:ao,self:mo},yo={color:Object,type:{type:String,default:"default"},round:Boolean,size:{type:String,default:"medium"},closable:Boolean,disabled:{type:Boolean,default:void 0}},Po=so("tag",`
 --n-close-margin: var(--n-close-margin-top) var(--n-close-margin-right) var(--n-close-margin-bottom) var(--n-close-margin-left);
 white-space: nowrap;
 position: relative;
 box-sizing: border-box;
 cursor: default;
 display: inline-flex;
 align-items: center;
 flex-wrap: nowrap;
 padding: var(--n-padding);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition: 
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 line-height: 1;
 height: var(--n-height);
 font-size: var(--n-font-size);
`,[p("strong",`
 font-weight: var(--n-font-weight-strong);
 `),x("border",`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
 border: var(--n-border);
 transition: border-color .3s var(--n-bezier);
 `),x("icon",`
 display: flex;
 margin: 0 4px 0 0;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 font-size: var(--n-avatar-size-override);
 `),x("avatar",`
 display: flex;
 margin: 0 6px 0 0;
 `),x("close",`
 margin: var(--n-close-margin);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),p("round",`
 padding: 0 calc(var(--n-height) / 3);
 border-radius: calc(var(--n-height) / 2);
 `,[x("icon",`
 margin: 0 4px 0 calc((var(--n-height) - 8px) / -2);
 `),x("avatar",`
 margin: 0 6px 0 calc((var(--n-height) - 8px) / -2);
 `),p("closable",`
 padding: 0 calc(var(--n-height) / 4) 0 calc(var(--n-height) / 3);
 `)]),p("icon, avatar",[p("round",`
 padding: 0 calc(var(--n-height) / 3) 0 calc(var(--n-height) / 2);
 `)]),p("disabled",`
 cursor: not-allowed !important;
 opacity: var(--n-opacity-disabled);
 `),p("checkable",`
 cursor: pointer;
 box-shadow: none;
 color: var(--n-text-color-checkable);
 background-color: var(--n-color-checkable);
 `,[I("disabled",[z("&:hover","background-color: var(--n-color-hover-checkable);",[I("checked","color: var(--n-text-color-hover-checkable);")]),z("&:active","background-color: var(--n-color-pressed-checkable);",[I("checked","color: var(--n-text-color-pressed-checkable);")])]),p("checked",`
 color: var(--n-text-color-checked);
 background-color: var(--n-color-checked);
 `,[I("disabled",[z("&:hover","background-color: var(--n-color-checked-hover);"),z("&:active","background-color: var(--n-color-checked-pressed);")])])])]),Io=Object.assign(Object.assign(Object.assign({},D.props),yo),{bordered:{type:Boolean,default:void 0},checked:Boolean,checkable:Boolean,strong:Boolean,triggerClickOnClose:Boolean,onClose:[Array,Function],onMouseenter:Function,onMouseleave:Function,"onUpdate:checked":Function,onUpdateChecked:Function,internalCloseFocusable:{type:Boolean,default:!0},internalCloseIsButtonTag:{type:Boolean,default:!0},onCheckedChange:Function}),zo=ko("n-tag"),$o=to({name:"Tag",props:Io,slots:Object,setup(l){const i=ho(null),{mergedBorderedRef:r,mergedClsPrefixRef:C,inlineThemeDisabled:c,mergedRtlRef:d}=go(l),s=D("Tag","-tag",Po,xo,l,C);bo(zo,{roundRef:Co(l,"round")});function n(){if(!l.disabled&&l.checkable){const{checked:o,onCheckedChange:a,onUpdateChecked:u,"onUpdate:checked":b}=l;u&&u(!o),b&&b(!o),a&&a(!o)}}function t(o){if(l.triggerClickOnClose||o.stopPropagation(),!l.disabled){const{onClose:a}=l;a&&fo(a,o)}}const f={setTextContent(o){const{value:a}=i;a&&(a.textContent=o)}},k=vo("Tag",d,C),g=U(()=>{const{type:o,size:a,color:{color:u,textColor:b}={}}=l,{common:{cubicBezierEaseInOut:m},self:{padding:S,closeMargin:B,borderRadius:$,opacityDisabled:H,textColorCheckable:R,textColorHoverCheckable:M,textColorPressedCheckable:T,textColorChecked:E,colorCheckable:_,colorHoverCheckable:j,colorPressedCheckable:O,colorChecked:W,colorCheckedHover:K,colorCheckedPressed:L,closeBorderRadius:A,fontWeightStrong:Q,[h("colorBordered",o)]:Y,[h("closeSize",a)]:q,[h("closeIconSize",a)]:G,[h("fontSize",a)]:J,[h("height",a)]:w,[h("color",o)]:X,[h("textColor",o)]:Z,[h("border",o)]:oo,[h("closeIconColor",o)]:F,[h("closeIconColorHover",o)]:eo,[h("closeIconColorPressed",o)]:ro,[h("closeColorHover",o)]:lo,[h("closeColorPressed",o)]:co}}=s.value,P=uo(B);return{"--n-font-weight-strong":Q,"--n-avatar-size-override":`calc(${w} - 8px)`,"--n-bezier":m,"--n-border-radius":$,"--n-border":oo,"--n-close-icon-size":G,"--n-close-color-pressed":co,"--n-close-color-hover":lo,"--n-close-border-radius":A,"--n-close-icon-color":F,"--n-close-icon-color-hover":eo,"--n-close-icon-color-pressed":ro,"--n-close-icon-color-disabled":F,"--n-close-margin-top":P.top,"--n-close-margin-right":P.right,"--n-close-margin-bottom":P.bottom,"--n-close-margin-left":P.left,"--n-close-size":q,"--n-color":u||(r.value?Y:X),"--n-color-checkable":_,"--n-color-checked":W,"--n-color-checked-hover":K,"--n-color-checked-pressed":L,"--n-color-hover-checkable":j,"--n-color-pressed-checkable":O,"--n-font-size":J,"--n-height":w,"--n-opacity-disabled":H,"--n-padding":S,"--n-text-color":b||Z,"--n-text-color-checkable":R,"--n-text-color-checked":E,"--n-text-color-hover-checkable":M,"--n-text-color-pressed-checkable":T}}),v=c?po("tag",U(()=>{let o="";const{type:a,size:u,color:{color:b,textColor:m}={}}=l;return o+=a[0],o+=u[0],b&&(o+=`a${V(b)}`),m&&(o+=`b${V(m)}`),r.value&&(o+="c"),o}),g,l):void 0;return Object.assign(Object.assign({},f),{rtlEnabled:k,mergedClsPrefix:C,contentRef:i,mergedBordered:r,handleClick:n,handleCloseClick:t,cssVars:c?void 0:g,themeClass:v==null?void 0:v.themeClass,onRender:v==null?void 0:v.onRender})},render(){var l,i;const{mergedClsPrefix:r,rtlEnabled:C,closable:c,color:{borderColor:d}={},round:s,onRender:n,$slots:t}=this;n==null||n();const f=N(t.avatar,g=>g&&y("div",{class:`${r}-tag__avatar`},g)),k=N(t.icon,g=>g&&y("div",{class:`${r}-tag__icon`},g));return y("div",{class:[`${r}-tag`,this.themeClass,{[`${r}-tag--rtl`]:C,[`${r}-tag--strong`]:this.strong,[`${r}-tag--disabled`]:this.disabled,[`${r}-tag--checkable`]:this.checkable,[`${r}-tag--checked`]:this.checkable&&this.checked,[`${r}-tag--round`]:s,[`${r}-tag--avatar`]:f,[`${r}-tag--icon`]:k,[`${r}-tag--closable`]:c}],style:this.cssVars,onClick:this.handleClick,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},k||f,y("span",{class:`${r}-tag__content`,ref:"contentRef"},(i=(l=this.$slots).default)===null||i===void 0?void 0:i.call(l)),!this.checkable&&c?y(io,{clsPrefix:r,class:`${r}-tag__close`,disabled:this.disabled,onClick:this.handleCloseClick,focusable:this.internalCloseFocusable,round:s,isButtonTag:this.internalCloseIsButtonTag,absolute:!0}):null,!this.checkable&&this.mergedBordered?y("div",{class:`${r}-tag__border`,style:{borderColor:d}}):null)}});export{$o as N,Bo as g};
