import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ResourcePoolDetailsComponent } from './resource_pool-details.component';

describe('TemplatesComponent', () => {
  let component: ResourcePoolDetailsComponent;
  let fixture: ComponentFixture<ResourcePoolDetailsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ResourcePoolDetailsComponent ]
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
