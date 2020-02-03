from date import daycount as dc


class BGM:
    def __init__(self, zero_curve, fwd_rates, displacement_beta, delta):
        self.zero_curve = zero_curve
        self.realized_fwd_rates = fwd_rates
        self.displacement_beta = displacement_beta
        self.delta = delta

    def T_q(self, date):
        """

        :param date: time variable
        :return: list containing: [T_(q(date)-1),T_q(date)]
        """
        q = []
        for i in range(len(self.realized_fwd_rates.index) - 1):
            if self.realized_fwd_rates.index[i] <= date < self.realized_fwd_rates.index[i + 1]:
                q.extend([self.realized_fwd_rates.index[i], self.realized_fwd_rates.index[i + 1]])
        return q

    def df_from_zero_curve_by_LI(self, date):
        """
        :param date: time variable
        :return: P(0,t) where we interpolated know points on the zero curve
        """
        fwd_rate_dates = self.T_q(date)
        left_date = fwd_rate_dates[0]
        right_date = fwd_rate_dates[1]
        left_value = self.zero_curve.loc[fwd_rate_dates[0]]
        right_value = self.zero_curve.loc[fwd_rate_dates[1]]
        df_value = left_value + (right_value - left_value) * dc.daydiff(left_date, date, 'ACTUAL/365 FIXED') / \
                   dc.daydiff(left_date, right_date, 'ACTUAL/365 FIXED')
        return df_value

    def fwd_rate_on_start_date(self, date_1, date_2):
        """
        Returns displaced L(0, date_1, date_2), L(0, date_1, date_2) + beta
        :param date_1: start period
        :param date_2: end period
        :return: Displaced forward rate observed from time 0 (start date) in the period [date_1, date_2]
        """
        df_1 = self.df_from_zero_curve_by_LI(date_1)
        df_2 = self.df_from_zero_curve_by_LI(date_2)
        fwd = (1 / dc.yearfrac(date_1, date_2, 'ACTUAL/365 FIXED')) * ((df_1 / df_2) - 1)
        return fwd + self.displacement_beta

    def alpha_tilde(self, date):
        """
        Calculates alpha_tilde on page 61
        :param date: time variable
        :return: alpha_tilde
        """
        T_q_t_min_1 = self.T_q(date)[0]
        T_q_t = self.T_q(date)[1]

        fwd_1 = self.fwd_rate_on_start_date(date, T_q_t)
        fwd_2 = self.fwd_rate_on_start_date(T_q_t_min_1, T_q_t)

        alpha = (dc.yearfrac(date, T_q_t, 'ACTUAL/365 FIXED') / self.delta) * (fwd_1 / fwd_2)
        return alpha

    def f_t(self, date):
        """

        :param date: time variable
        :return: f_t on p62
        """
        T_q_t_min_1 = self.T_q(date)[0]
        T_q_t = self.T_q(date)[1]

        fwd_1 = self.fwd_rate_on_start_date(date, T_q_t)
        fwd_2 = self.fwd_rate_on_start_date(T_q_t_min_1, T_q_t)
        return fwd_1 / fwd_2

    def df_from_closest_next_tenor_to_t(self, date):
        """
        Returns P(date, T_q(date)), see (3.26) on page 62
        :param date: time variable
        with the index equal to the fixing dates
        :return: Discount factor
        """
        T_q_t_min_1 = self.T_q(date)[0]
        T_q_t = self.T_q(date)[1]

        denumerator = 1 + dc.yearfrac(date, T_q_t, 'ACTUAL/365 FIXED') * \
                      (self.f_t(date) * self.realized_fwd_rates.loc[T_q_t_min_1, 'fwd'] - self.displacement_beta)
        return 1 / denumerator

    def df_between_tenors(self, tenor_date_1, tenor_date_2):
        """
        Returns P(tenor_date_1, tenor_date_2)
        :param tenor_date_1: Left tenor date
        :param tenor_date_2: Right tenor date
        :return: Discount factor from a tenor date to the previous tenor date
        """
        tenor_dates_including = self.realized_fwd_rates.loc[tenor_date_1:tenor_date_2, 'fwd'].index.values
        denominator = 1
        for tenor_date in tenor_dates_including[:-1]:
            denominator = denominator * (1 + self.delta * self.realized_fwd_rates.loc[tenor_date, 'fwd'])
        return 1 / denominator

    def df_from_T_to_t_BERT(self, date, end_T):
        """
        Return P(date, T), where t<=T
        :param date: Time variable
        :param end_T: Time variable where t<=T
        :return: Discount factor from time T to time date
        """
        T_q_t = self.T_q(date)[1]
        T_q_T_min_1 = self.T_q(end_T)[0]
        T_q_T = self.T_q(end_T)[1]

        df_from_T_q_T_min_1_to_t = self.df_from_closest_next_tenor_to_t(date) * \
                                   self.df_between_tenors(T_q_t, T_q_T_min_1)
        df_from_T_q_T_to_t = self.df_from_closest_next_tenor_to_t(date) * \
                             self.df_between_tenors(T_q_t, T_q_T)
        if date <= T_q_T_min_1:
            alpha_1_T = self.alpha_tilde(end_T)
            first_part = alpha_1_T * df_from_T_q_T_min_1_to_t
            second_part = (1 - alpha_1_T) * df_from_T_q_T_to_t
            third_part = self.displacement_beta * \
                         (self.delta * alpha_1_T - dc.yearfrac(end_T, T_q_T, 'ACTUAL/365 FIXED')) * df_from_T_q_T_to_t
            return first_part + second_part + third_part
        elif date > T_q_T_min_1:
            alpha_2_T = self.alpha_tilde(end_T) / self.alpha_tilde(date)
            first_part = alpha_2_T
            second_part = (1 - alpha_2_T) * df_from_T_q_T_to_t
            third_part = self.displacement_beta * \
                         (dc.yearfrac(date, T_q_T, 'ACTUAL/365 FIXED')
                          * alpha_2_T - dc.yearfrac(T, T_q_T, 'ACTUAL/365 FIXED')) * df_from_T_q_T_to_t
            return first_part + second_part + third_part

