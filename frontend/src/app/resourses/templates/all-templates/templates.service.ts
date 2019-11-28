import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class TemplatesService {

    constructor(private service: Apollo) {}

    public getAllTemplates(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms {
                                templates {
                                    veil_info
                                }
                            }
                        `,
            variables: {
                method: 'GET'
            }
        });
    }

    public getTemplate(id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query Template($id: String) {
                            template(id: $id) {
                               info
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id
            }
        });
    }
}
