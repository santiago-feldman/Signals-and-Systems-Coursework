function wk=kai(N,alfa)
%Hallo la ventana de kaiser

for n=0:(N-1)/2
beta=alfa*sqrt(1-((2*n)/(N-1))^2);
wk(n+1)=io(beta)/io(alfa);
end
wk=[wk(((N-1)/2)+1:-1:2) wk]';
