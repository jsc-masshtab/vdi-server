import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class DatapoolsService {

    constructor(private service: Apollo) {}

    public getAllDatapools(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query allDatapools {
                            controllers {
                                datapools {
                                    id
                                    used_space
                                    free_space
                                    size
                                    status
                                    type
                                    vdisk_count
                                    file_count
                                    iso_count
                                    verbose_name
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    public getDatapool(idDatapool: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query Datapool($id: String) {
                            datapool(id: $id) {
                                used_space
                                free_space
                                size
                                status
                                type
                                vdisk_count
                                file_count
                                iso_count
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id: idDatapool
            }
        });
    }
}


