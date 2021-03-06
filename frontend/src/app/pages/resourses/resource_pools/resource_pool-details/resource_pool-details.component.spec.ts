import { NO_ERRORS_SCHEMA, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { ResourcePoolsService } from '../all-resource_pools/resource_pools.service';
import { ResourcePoolDetailsComponent } from './resource_pool-details.component';

describe('ResourcePoolDetailsComponent', () => {
  let component: ResourcePoolDetailsComponent;
  let fixture: ComponentFixture<ResourcePoolDetailsComponent>;

  let serviceStub: Partial<ResourcePoolsService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getResourcePool(): any {
        return {
          valueChanges: of({
            data: {
              resource_pool: []
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ ResourcePoolDetailsComponent ],
      providers: [
        {
          provide: ResourcePoolsService,
          useValue: serviceStub
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ResourcePoolDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
