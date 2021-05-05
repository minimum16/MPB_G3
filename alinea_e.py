import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import ode
from scipy.optimize import basinhopping


def jm109(t, y, params):
    '''
    This will be the model for the strain JM109 which is similar to the BL21, but it should have slight modifications
    :param t: time; This argument should not be altered
    :param Y: initial conditions; array-like data structure (list, tuple, numpy array)
    :param params: parameters; array-like data structure (list, tuple, numpy array) - NOTE THAT THESE ARGUMENT MUST
    CONTAIN ONLY AND ONLY THOSE PARAMETERS TO BE ESTIMATED. The remain parameters should be hardcoded within the
    function
    :return: K * phi - (D * variables) + zeros; note that numpy.dot() is the standard for matrices multiplication
    '''

    X, S, A, P, V = y
    k4, u2, Ks3 = params

    u1 = 0.25 * (S / (0.3 + S))
    u3 = 0.25 * (A / (Ks3 + A))

    D = 0.7 / V
    reac = [u1 * X + u2 * X + u3 * X - D * X, -4.412 * u1 * X - 22.22 * u2 * X - D * S + D * 350, 8.61 * u2 * X - k4 * u3 * X - D * A, 13.21 * u1 * X - D * P, 0.7]  # X, S, A, P, V || usando as reacoes de crescimento
    return reac


# Initial conditions
X0= 1 #g/L  BL21=4  dados_exp=1
S0= 0 #g/L
A0= 0 #g/L
P0= 0 #g/L
V= 3 #L  BL21=8  dados_exp=3

#lista com os valores iniciais fornecida a func
y0= [X0, S0, A0, P0, V]

#lista com os parametros fornecida a func
#params_old= [k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, V0, Fe, Se]
k4= 9.846
u2 = 0.55 * (0 / (0.3 + 0))
Ks3= 0.4
params= [k4, u2, Ks3]

# Final time and step
t0= 0 #tempo inicial
t= 20 #tempo final
dt= 0.5 #intervalo de tempo entre reads
#linspace


def estimate(params):
    """
    This will be our estimate function that works out as the calculation of the difference between the experimental
    and predicted values and can be used as the objective function

    :param params: parameters; array-like data structure (list, tuple, numpy array) for the ode
    :return: the error between measured and predicted data, i.e. difS + difX + difA + difV
    """

    global model
    global t
    global t0
    global dt
    global dados_exp
    global y0
    global Y
    global soma1
    global coisa

    r = ode(model).set_integrator('lsoda', method='bdf', lband=0, nsteps=5000)  # lband é o limite inferior -- para nao haver valores negativos
    r.set_initial_value(y0, t0).set_f_params(params)

    Y = [[1, 0, 0, 0, 3]] #variavel Y com os dados iniciais

    while r.successful() and r.t < t:
        time = r.t + dt
        Y.append(r.integrate(time).tolist())

    for i in range(len(Y)): #retira a coluna da proteina(P) para ter uma matriz igual à dos dados experimentais
        Y[i].pop(3)

    if len(Y) == len(dados_exp): #a função só vai executar isto quando os tamanhos das 2 matrizes forem iguais
        #isto é necessário porque a ODE estava a terminar com uma matriz com menos linhas e não permitia a execução do erro
        #o anterior acontecia porque a ODE não estava a conseguir integrar com sucesso (while r.successful no chunk acima)
        #para evitar isto fizemos com que o basinhopping use os valores anteriores da ODE caso a atual execução da mesma dê o tal erro
        coisa= Y #guardar numa variavel diferente para no final conseguir usar a matriz dos estimados sem as falhas faladas anteriormente
        #diferenca= np.subtract(Y, dados_exp)
        diferenca = np.subtract(coisa, dados_exp) #diferença entre os valores
        po = np.power(diferenca, 2) #diferença ao quadrado
        soma= po.sum(axis=0) #soma dos quadrados das diferenças
        soma1= soma.sum() #soma das somas dos quadrados das diferenças
    return soma1 #soma dos quadrados das diferenças


model = jm109

#t = timespan
#Final time and step

dados_exp= pd.read_excel('dados_exp.xlsx').to_numpy().tolist()
for i in range(len(dados_exp)): #retira a coluna do tempo(T) para ter uma matriz igual à Y dos estimados
    dados_exp[i].pop(0)



# Bounds
# Consider using the following class for setting the Simulated Annealing bounds
class Bounds(object):

    def __init__(self, LB=None, UB=None):

        if LB is None:
            LB = [0, 0, 0]

        if UB is None:
            UB = [4, 4, 4]

        self.lower_bound = np.array(LB)
        self.upper_bound = np.array(UB)

    def __call__(self, **kwargs):

        x = kwargs["x_new"]

        tmax = bool(np.all(x <= self.upper_bound))
        tmin = bool(np.all(x >= self.lower_bound))

        return tmax and tmin


#Bounds
LB = [0, 0, 0]
UB = [4, 4, 4]
bounds = Bounds(LB, UB)

# initial guess, that is the initial values for the parameters to be estimated. It can be those available in the pdf
x0 = [9.846, 0.55 * (0 / (0.3 + 0)), 0.4]

minimizer_kwargs = {"method": "Nelder-Mead"} #method BFGS -- não funfou

#for_real= basinhopping(estimate, x0, minimizer_kwargs= minimizer_kwargs, niter= 200, accept_test= bounds, seed= 1)
tentar= basinhopping(estimate, x0, minimizer_kwargs= minimizer_kwargs, accept_test= bounds, niter=10, seed=1, disp=True)
print(tentar)


#######graficos
Yx, Ys, Ya, Yv=[], [], [], []
DEx, DEs, DEa, DEv=[], [], [], []
T=[0]


for i in range(40): #criar a lista com os tempos para fazer os graficos
    T.append(T[i]+0.5)

for i in range(len(coisa)): #separar as colunas da matriz dos estimados para obter os valores para fazer o grafico
    Yx.append(coisa[i][0])
    Ys.append(coisa[i][1])
    Ya.append(coisa[i][2])
    Yv.append(coisa[i][3])

for i in range(len(dados_exp)): #separar as colunas da matriz dos dados experimentais para obter os valores para fazer o grafico
    DEx.append(dados_exp[i][0])
    DEs.append(dados_exp[i][1])
    DEa.append(dados_exp[i][2])
    DEv.append(dados_exp[i][3])

#plot do grafico do estimado
plt.plot(T, Yx, label='Biomassa', color='blue')
plt.plot(T, Ys, label='Substrato', color='red')
plt.plot(T, Ya, label='Acetato', color='green')
plt.plot(T, Yv, label='Volume (L)', color='Purple')
plt.legend(loc='best')
plt.xlabel('Tempo (h)')
plt.ylabel('Concentração (g/L)')
#plt.xlim(0, 1)
#plt.ylim(0, 30)
plt.grid()
plt.show()

#plot do grafico dos dados experimentais
plt.plot(T, DEx, label='Biomassa', color='blue')
plt.plot(T, DEs, label='Substrato', color='red')
plt.plot(T, DEa, label='Acetato', color='green')
plt.plot(T, DEv, label='Volume (L)', color='Purple')
plt.legend(loc='best')
plt.xlabel('Tempo (h)')
plt.ylabel('Concentração (g/L)')
#plt.xlim(0, 1)
#plt.ylim(0, 30)
plt.grid()
plt.show()