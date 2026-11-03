const cl=(x)=>Math.max(0,Math.min(1,x)),ease=(x)=>1-Math.pow(1-cl(x),3),eio=(x)=>{x=cl(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2},back=(x)=>{x=cl(x);const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const $=(id)=>document.getElementById(id);
const pop=(el,t,t0,d=.5,dy=60)=>{const a=ease((t-t0)/d);el.style.opacity=a;el.style.transform=(el.dataset.tf||'')+` translateY(${(1-a)*dy}px)`;return a};
const out=(t,t0,d=.4)=>1-cl((t-t0)/d);
