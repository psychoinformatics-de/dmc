import os
from os.path import join as opj
from os.path import exists
import json

public_data_path = '/tmp/records/public/datascience'
private_data_path = '/tmp/records/private/datascience'
figure_path = 'www/datascience/stats'


def load_data(public=public_data_path, private=private_data_path):
    data = []
    for id_ in os.listdir(public):
        pubd = json.load(open(opj(public, id_)))
        privd = json.load(open(opj(private, id_)))
        # merge
        pubd.update(privd)
        pubd['id'] = id_
        rec = dict([(k, v) for k, v in pubd.items()
                    if v != ''])
        data.append(rec)
    return data


def data2df(data):
    import pandas as pd
    df = pd.DataFrame.from_records(data, index='id')
    # type conversion
    # numeric
    for c in ('collaborations',
              'collaborations_data',
              'collaborations_data_provided',
              'data_consumed_public',
              'data_shared_publicly_num',
              'server_version',
              'client_version',
              ):
        df[c] = pd.to_numeric(df[c])
    # date
    for c in ('submit_date',):
        df[c] = pd.to_datetime(df[c])
    # bool
    for c in ('data_download_difficult',
              'data_products',
              'data_publish_difficult',
              'data_published_paper',
              'data_search',
              'data_search_use',
              'data_shared_publicly_ever',
              'atlases',
              'bids',
              'data_IRB',
              'neurovault_search',
              'neurovault_uploads',
              'common_description',
              'result_search',
              'result_uploads',
              'vcs_code',
              'vcs_data',):
        df[c] = pd.to_numeric(
            [i == 'Yes' if not i is pd.np.nan else pd.np.nan for i in df[c]],
            downcast='integer')
    return df


def make_figures(df, outdir):
    import pylab as pl
    import seaborn as sns
    pl.figure()
    sns.countplot(y='OS', data=df)
    pl.xlabel('Number of submissions')
    pl.ylabel('Primary operating system')
    pl.savefig(opj(outdir, 'sub_by_os.png'))


if __name__ == '__main__':
    data = load_data()
    df = data2df(data)
    if not exists(figure_path):
        os.makedirs(figure_path)
    make_figures(df, figure_path)
