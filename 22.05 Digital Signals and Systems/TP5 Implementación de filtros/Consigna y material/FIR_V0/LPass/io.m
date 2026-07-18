function  io=besl(x)

%Calculo de la funcion de bessel de orden cero de primer especie
%segun la serie Io(x)=1+sum(1/k!*(x/2)^k)^2

io=1;
oldio=0;
error=1e-9;	%Modificar este valor de acuerdo con el grado de aprox. necesario
k=1;
while(abs(io-oldio)>error)
new=((1/fact(k))*(x/2)^k)^2;
oldio=io;
io=io+new;
k=k+1;
end

